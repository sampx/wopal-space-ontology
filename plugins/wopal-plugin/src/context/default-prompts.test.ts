import { describe, expect, it } from "vitest";
import {
  COMMIT_MSG_FALLBACK,
  DEDUP_FALLBACK,
  EXTRACTION_FALLBACK,
  TITLE_FALLBACK,
} from "./default-prompts.js";

describe("built-in prompt defaults", () => {
  it("carries the full title template with its placeholder", () => {
    expect(TITLE_FALLBACK).toContain("{{summary}}");
    expect(TITLE_FALLBACK).toContain("<rules>");
    expect(TITLE_FALLBACK).toContain("<examples>");
    expect(TITLE_FALLBACK.length).toBeGreaterThan(1000);
  });

  it("carries the full extraction template with its placeholder", () => {
    expect(EXTRACTION_FALLBACK).toContain("{{conversation}}");
    expect(EXTRACTION_FALLBACK).toContain("# Category System");
    expect(EXTRACTION_FALLBACK).toContain("# Category Decision Tree");
    expect(EXTRACTION_FALLBACK).toContain("# Tags Specification");
    expect(EXTRACTION_FALLBACK.length).toBeGreaterThan(10000);
  });

  it("carries the full dedup template with its placeholder", () => {
    expect(DEDUP_FALLBACK).toContain("{{input}}");
    expect(DEDUP_FALLBACK).toContain("## create Rules");
    expect(DEDUP_FALLBACK).toContain("## replace Rules");
    expect(DEDUP_FALLBACK.length).toBeGreaterThan(3000);
  });

  it("carries the full commit-message template with its placeholder", () => {
    expect(COMMIT_MSG_FALLBACK).toContain("${gitContext}");
    expect(COMMIT_MSG_FALLBACK).toContain("## Type Selection Rules");
    expect(COMMIT_MSG_FALLBACK).toContain("## Character Limits");
    expect(COMMIT_MSG_FALLBACK).toContain("## Issue Reference Rules");
  });
});
