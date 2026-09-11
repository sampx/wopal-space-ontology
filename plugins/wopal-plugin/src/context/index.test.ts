import { describe, expect, it } from "vitest";
import {
  DistillEngine,
  loadExtractionState,
  clearExtractionState,
  getPendingConfirmation,
  setPendingConfirmation,
  clearPendingConfirmation,
  loadSessionContext,
  saveSessionContext,
  clearSessionContext,
  getSessionContextDir,
  cleanupLegacyStateFiles,
  createContextPrompts,
  buildExtractionPrompt,
  loadTitlePrompt,
} from "./index.js";

describe("context module public API", () => {
  it("exposes the distill engine and its state helpers", () => {
    expect(typeof DistillEngine).toBe("function");
    expect(typeof loadExtractionState).toBe("function");
    expect(typeof clearExtractionState).toBe("function");
    expect(typeof getPendingConfirmation).toBe("function");
    expect(typeof setPendingConfirmation).toBe("function");
    expect(typeof clearPendingConfirmation).toBe("function");
  });

  it("exposes the session context store", () => {
    expect(typeof loadSessionContext).toBe("function");
    expect(typeof saveSessionContext).toBe("function");
    expect(typeof clearSessionContext).toBe("function");
    expect(typeof getSessionContextDir).toBe("function");
    expect(typeof cleanupLegacyStateFiles).toBe("function");
  });

  it("exposes the title and extraction prompt builders", () => {
    expect(typeof createContextPrompts).toBe("function");
    expect(typeof buildExtractionPrompt).toBe("function");
    expect(typeof loadTitlePrompt).toBe("function");
  });

  it("keeps the session context storage path unchanged", () => {
    expect(getSessionContextDir("/tmp/wopal-home")).toBe(
      "/tmp/wopal-home/storage/session_context",
    );
  });

  it("tracks pending confirmations in-process", () => {
    const sessionID = `ses-${crypto.randomUUID()}`;
    expect(getPendingConfirmation(sessionID)).toBeUndefined();
    setPendingConfirmation(sessionID, { candidates: [], title: "t" });
    expect(getPendingConfirmation(sessionID)).toEqual({ candidates: [], title: "t" });
    clearPendingConfirmation(sessionID);
    expect(getPendingConfirmation(sessionID)).toBeUndefined();
  });
});
