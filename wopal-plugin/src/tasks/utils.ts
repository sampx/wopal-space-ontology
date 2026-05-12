/**
 * Shared utility functions for the tasks module.
 */

export function toErrorMessage(error: unknown): string {
  if (error instanceof Error && error.message) {
    return error.message
  }

  if (typeof error === "string" && error.length > 0) {
    return error
  }

  try {
    const serialized = JSON.stringify(error)
    if (serialized && serialized !== "{}") {
      return serialized
    }
  } catch {
    // Ignore JSON serialization failures and fall back to String().
  }

  return String(error)
}

export function isPromiseLike(value: unknown): value is PromiseLike<unknown> {
  return typeof value === "object" && value !== null && "then" in value
}
