const BASE62 = /^[0-9A-Za-z]+$/;
export const isBase62 = (s: string) => BASE62.test(s);
export const isLen10 = (s: string) => s.length === 10;
export const isSortedAfter = (prev: string, cur: string) => cur > prev;
export const validateId = (s: string) => ({ len: isLen10(s), charset: isBase62(s) });

export function summarize(ids: string[]) {
  let invalid = 0;
  let sortedOk = true;
  for (let i = 0; i < ids.length; i++) {
    const v = validateId(ids[i]);
    if (!v.len || !v.charset) invalid++;
    if (i > 0 && !isSortedAfter(ids[i - 1], ids[i])) sortedOk = false;
  }
  return { total: ids.length, valid: ids.length - invalid, invalid, sortedOk };
}
