/**
 * Task ID resolver — deterministic multi-mode task matching with ambiguity
 * hard-blocking.
 *
 * Background: compaction summaries truncate long task IDs (e.g.
 * `wopal-task-1bcbb6eacffeD6Mr5eedcZH1hZ` → `wopal-task-1bcbb6eacffe`), and
 * debug logs print trailing hash fragments via `formatSessionID` (e.g.
 * `D6Mr5eedcZH1hZ(task)`). This resolver lets callers accept such truncated
 * references while refusing to guess when a query matches more than one task.
 *
 * Matching order: exact → prefix → suffix → normalized (decoration-stripped
 * body). A candidate hit by multiple modes is deduplicated; when the union of
 * all fuzzy candidates contains ≥ 2 tasks the result is `ambiguous` (never
 * guess).
 */

import type { WopalTask } from "../types.js"

/** Minimum query length (after trimming) for fuzzy matching to be attempted. */
export const MIN_FUZZY_QUERY_LENGTH = 3

/** How a fuzzy (non-exact) match identified the task. */
export type FuzzyMatchMode = "prefix" | "suffix" | "normalized"

export type TaskResolveResult<T extends { id: string }> =
  | { type: "exact"; task: T }
  | { type: "unique"; task: T; matchedBy: FuzzyMatchMode }
  | { type: "ambiguous"; query: string; candidates: T[] }
  | { type: "not_found"; query: string; availableTasks: T[] }

/** ID decorations stripped before body (normalized) matching. */
const ID_DECORATIONS = ["wopal-task-", "ses_"] as const
/** Trailing role decoration produced by `formatSessionID` (e.g. `abc(task)`). */
const TRAILING_ROLE_SUFFIX = /\((?:task|main)\)$/

function stripDecorations(value: string): string {
  let stripped = value
  for (const decoration of ID_DECORATIONS) {
    stripped = stripped.replace(decoration, "")
  }
  return stripped
}

/**
 * Decoration-stripped hash body of a task. Derived from the task ID itself —
 * by construction (`sessionIDToTaskID`) a task ID already carries the same
 * hash as its session, so the ID is the single source of truth here.
 */
function bodyOf(task: { id: string }): string {
  return stripDecorations(task.id)
}

/** Query body after removing log decorations (`(task)`/`(main)`) and ID prefixes. */
function bodyOfQuery(query: string): string {
  return stripDecorations(query.replace(TRAILING_ROLE_SUFFIX, ""))
}

/**
 * Resolve a user-provided task reference against a task collection.
 *
 * Returns a structured verdict instead of throwing or silently guessing:
 * - `exact` — query equals a task's full ID;
 * - `unique` — exactly one task fuzzy-matches (prefix/suffix/normalized);
 * - `ambiguous` — ≥ 2 tasks fuzzy-match; candidates are returned, no guessing;
 * - `not_found` — nothing matched; availableTasks supports diagnostic output.
 *
 * Queries shorter than {@link MIN_FUZZY_QUERY_LENGTH} chars only resolve via
 * exact match.
 */
export function resolveTask<T extends { id: string; sessionID?: string }>(
  tasks: Iterable<T>,
  query: string,
): TaskResolveResult<T> {
  const trimmed = query.trim()
  const allTasks = [...tasks]

  // 1) Exact match wins over everything.
  const exact = allTasks.find((task) => task.id === trimmed)
  if (exact) {
    return { type: "exact", task: exact }
  }

  // Empty or too-short queries refuse fuzzy matching entirely.
  if (trimmed.length === 0 || trimmed.length < MIN_FUZZY_QUERY_LENGTH) {
    return { type: "not_found", query: trimmed, availableTasks: allTasks }
  }

  const queryBody = bodyOfQuery(trimmed)

  // 2) Fuzzy: collect the union of prefix / suffix / normalized hits.
  //    All three modes are evaluated per task (not else-if chained) so a query
  //    that is a prefix of one task and a suffix of another still yields 2
  //    candidates → ambiguous, instead of silently masking the second hit.
  //
  //    Mode semantics (first hit wins per task):
  //    - "prefix"      — query starts the raw task ID (compaction truncation);
  //    - "normalized"  — query equals the entire decoration-stripped body
  //                      (bare full hash or `ses_<hash>` form);
  //    - "suffix"      — query ends the raw task ID (log tail fragment);
  //    - fallback      — fragment resolved via decoration-stripped body;
  //                      log-style refs (`<hash>(task)`) count as "suffix".
  const matchedBy = new Map<T, FuzzyMatchMode>()
  for (const task of allTasks) {
    const body = bodyOf(task)
    let mode: FuzzyMatchMode | undefined
    if (task.id.startsWith(trimmed)) {
      mode = "prefix"
    } else if (body.length > 0 && queryBody === body) {
      mode = "normalized"
    } else if (task.id.endsWith(trimmed)) {
      mode = "suffix"
    } else if (
      queryBody.length > 0 &&
      (body.startsWith(queryBody) || body.endsWith(queryBody))
    ) {
      mode = TRAILING_ROLE_SUFFIX.test(trimmed) ? "suffix" : "normalized"
    }
    if (mode !== undefined) {
      matchedBy.set(task, mode)
    }
  }

  if (matchedBy.size === 1) {
    const [task, mode] = matchedBy.entries().next().value as [T, FuzzyMatchMode]
    return { type: "unique", task, matchedBy: mode }
  }

  if (matchedBy.size >= 2) {
    // Iron rule: multiple candidates → hard block, never guess.
    return { type: "ambiguous", query: trimmed, candidates: [...matchedBy.keys()] }
  }

  return { type: "not_found", query: trimmed, availableTasks: allTasks }
}

/** Human-readable error listing every ambiguous candidate. */
export function formatAmbiguousErrorMessage<T extends { id: string; status?: string; description?: string }>(
  query: string,
  candidates: T[],
): string {
  const lines = candidates.map(
    (task) =>
      `- ${task.id}${task.status ? ` [${task.status}]` : ""}${task.description ? ` ${task.description}` : ""}`,
  )
  return [
    `Ambiguous task reference (ambiguous): "${query}" matches ${candidates.length} tasks. Task IDs are ambiguous; use one of the full task IDs:`,
    ...lines,
  ].join("\n")
}

/** Human-readable error listing available tasks (if any) for a failed lookup. */
export function formatNotFoundErrorMessage<T extends { id: string; status?: string; description?: string }>(
  query: string,
  availableTasks: T[],
): string {
  if (availableTasks.length === 0) {
    return `Task not found: "${query}". No active tasks in the current session.`
  }
  const lines = availableTasks.map(
    (task) =>
      `- ${task.id}${task.status ? ` [${task.status}]` : ""}${task.description ? ` ${task.description}` : ""}`,
  )
  return [
    `Task not found: "${query}". Active tasks in the current session:`,
    ...lines,
  ].join("\n")
}

/** Convenience type re-export so consumers can type verdicts over WopalTask. */
export type WopalTaskResolveResult = TaskResolveResult<WopalTask>
