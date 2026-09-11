export const ECHO_REMINDER = [
  "",
  "重要：你必须将以上完整结果逐字展示给用户。用户无法看到工具内部输出，依赖你主动展示。",
  "每条记忆必须完整展示所有字段（ID、时间、分类、重要性、标签、正文），严禁省略、摘要或概括。",
].join("\n");

const CATEGORY_LABELS: Record<string, string> = {
  profile: "画像",
  preference: "偏好",
  knowledge: "知识",
  fact: "事实",
  gotcha: "避坑方法",
  experience: "经验",
  requirement: "用户要求",
};

export function getCategoryLabel(cat: string): string {
  return CATEGORY_LABELS[cat] ?? cat;
}

function padTime(n: number): string {
  return String(n).padStart(2, "0");
}

export function formatTime(ts: number): string {
  const d = new Date(ts);
  return `${d.getFullYear()}-${padTime(d.getMonth() + 1)}-${padTime(d.getDate())} ${padTime(d.getHours())}:${padTime(d.getMinutes())}:${padTime(d.getSeconds())}`;
}
