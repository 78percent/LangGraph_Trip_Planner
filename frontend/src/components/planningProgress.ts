export type PlanningStatus = "running" | "complete" | "error";

export function getPlanningProgress(
  messages: string[],
  status: PlanningStatus,
) {
  const lookups = new Set<string>();
  let completed = 0;
  let label = "正在寻找景点、天气与住宿";
  for (const message of messages) {
    if (["景点查询完成", "天气查询完成", "酒店查询完成"].includes(message)) {
      lookups.add(message);
      if (lookups.size === 3 && completed < 1) {
        completed = 1;
        label = "正在安排每天的旅行路线";
      }
    } else if (message === "行程草案已生成") {
      completed = Math.max(completed, 2);
      label = "正在核对地点、时间与预算";
    } else if (message === "正在修正行程校验问题…") {
      completed = 2;
      label = "正在微调行程，让安排更合理";
    } else if (message === "预算与事实整理完成") {
      completed = 3;
      label = "正在保存你的旅行计划";
    }
  }
  if (status === "complete") return { completed: 4, label: "旅行计划已保存" };
  if (status === "error") label = "本次规划未完成";
  return { completed, label };
}
