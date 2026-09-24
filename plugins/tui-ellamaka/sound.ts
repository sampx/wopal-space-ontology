/**
 * Sound effects for the WopalSpace branding slot.
 *
 * Kept independent from the animation module: the component spawns/stop the
 * hum on hold and plays a pulse on burst, but the sounds themselves are just
 * `afplay` invocations over the bundled asset pack.
 */

import { join } from "node:path";

const ASSET_DIR = import.meta.dir + "/asset";
const PULSE_FILES = ["pulse-a.wav", "pulse-b.wav", "pulse-c.wav"];

let humProc: ReturnType<typeof Bun.spawn> | undefined;
let shot = 0;

export function soundStart() {
  soundStop();
  try {
    humProc = Bun.spawn(["afplay", join(ASSET_DIR, "charge.wav")], {
      stdin: "ignore",
      stdout: "ignore",
      stderr: "ignore",
    });
  } catch {}
}

export function soundStop() {
  if (!humProc) return;
  try {
    humProc.kill();
  } catch {}
  humProc = undefined;
}

export function soundPulse(_volume = 1) {
  const file = PULSE_FILES[shot++ % PULSE_FILES.length];
  try {
    Bun.spawn(["afplay", join(ASSET_DIR, file)], {
      stdin: "ignore",
      stdout: "ignore",
      stderr: "ignore",
    });
  } catch {}
}

export function soundDispose() {
  soundStop();
}
