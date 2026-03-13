export function preview(text: string, limit: number): string {
  const cleaned = text.split(/\s+/).join(" ");
  return cleaned.length > limit ? cleaned.slice(0, limit) + "..." : cleaned;
}

export function lineNumber(text: string, index: number): number {
  return text.slice(0, index).split("\n").length;
}

export function lineContext(text: string, index: number, width: number): string {
  const lineStart = text.lastIndexOf("\n", index - 1) + 1;
  let lineEnd = text.indexOf("\n", index);
  if (lineEnd === -1) lineEnd = text.length;
  const line = text.slice(lineStart, lineEnd);
  const column = index - lineStart;

  let displayLine: string;
  let caretPos: number;

  if (line.length > width) {
    const half = Math.floor(width / 2);
    let left = Math.max(column - half, 0);
    let right = Math.min(left + width, line.length);
    if (right - left < width) left = Math.max(right - width, 0);
    const trimmed = line.slice(left, right);
    caretPos = column - left;
    const prefix = left > 0 ? "..." : "";
    const suffix = right < line.length ? "..." : "";
    displayLine = `${prefix}${trimmed}${suffix}`;
    caretPos += prefix.length;
  } else {
    displayLine = line;
    caretPos = column;
  }

  return `${displayLine}\n${" ".repeat(caretPos)}^`;
}
