import { describe, it, expect } from "vitest";
import { isBase62, isLen10, summarize } from "./validate";

describe("validate", () => {
  it("accepts base62 length-10", () => {
    expect(isBase62("0uLvI2MYQL")).toBe(true);
    expect(isLen10("0uLvI2MYQL")).toBe(true);
  });
  it("rejects non-base62 / wrong length", () => {
    expect(isBase62("0uLvI2-MYQ")).toBe(false);
    expect(isLen10("short")).toBe(false);
  });
  it("summarize counts invalid and sort order", () => {
    const s = summarize(["0000000001", "0000000002", "bad_id!!"]);
    expect(s.total).toBe(3);
    expect(s.invalid).toBe(1);
    expect(s.sortedOk).toBe(true);
  });
});
