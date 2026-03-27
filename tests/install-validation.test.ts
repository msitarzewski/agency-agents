import { describe, it, expect } from "vitest";
import { execSync } from "node:child_process";
import * as fs from "node:fs";
import * as path from "node:path";

const ROOT = path.resolve(__dirname, "..");
const SCRIPTS_DIR = path.join(ROOT, "scripts");

describe("Install validation", () => {
  describe("scripts/install.sh", () => {
    const installSh = path.join(SCRIPTS_DIR, "install.sh");

    it("should exist", () => {
      expect(fs.existsSync(installSh)).toBe(true);
    });

    it("should pass bash syntax check (bash -n)", () => {
      const result = execSync(`bash -n "${installSh}" 2>&1`, {
        encoding: "utf-8",
        timeout: 10_000,
      });
      // bash -n produces no output on success
      expect(result.trim()).toBe("");
    });
  });

  describe("scripts/install.ps1", () => {
    const installPs1 = path.join(SCRIPTS_DIR, "install.ps1");

    it.todo(
      "should exist (PowerShell install script not yet available)"
    );
  });

  describe("scripts/convert.sh", () => {
    const convertSh = path.join(SCRIPTS_DIR, "convert.sh");

    it("should exist", () => {
      expect(fs.existsSync(convertSh)).toBe(true);
    });

    it("should pass bash syntax check (bash -n)", () => {
      const result = execSync(`bash -n "${convertSh}" 2>&1`, {
        encoding: "utf-8",
        timeout: 10_000,
      });
      expect(result.trim()).toBe("");
    });
  });
});
