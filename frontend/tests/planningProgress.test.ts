import assert from "node:assert/strict";
import test from "node:test";
import { getPlanningProgress } from "../src/components/planningProgress.ts";

test("parallel lookup completion is order independent and deduplicated", () => {
  assert.equal(getPlanningProgress([], "running").completed, 0);
  assert.equal(
    getPlanningProgress(
      ["酒店查询完成", "酒店查询完成", "景点查询完成"],
      "running",
    ).completed,
    0,
  );
  assert.equal(
    getPlanningProgress(
      ["酒店查询完成", "景点查询完成", "天气查询完成"],
      "running",
    ).completed,
    1,
  );
});

test("validation retries stay in verification, and saving waits for a real result", () => {
  assert.equal(getPlanningProgress(["行程草案已生成"], "running").completed, 2);
  const retry = getPlanningProgress(
    [
      "行程草案已生成",
      "行程校验完成",
      "正在修正行程校验问题…",
      "行程草案已生成",
    ],
    "running",
  );
  assert.equal(retry.completed, 2);
  assert.equal(
    getPlanningProgress(["预算与事实整理完成"], "running").completed,
    3,
  );
  assert.equal(
    getPlanningProgress(["预算与事实整理完成"], "complete").completed,
    4,
  );
});

test("an error never claims completion and unknown events are not counted", () => {
  assert.equal(
    getPlanningProgress(["unknown", "hello"], "running").completed,
    0,
  );
  const failed = getPlanningProgress(["行程草案已生成"], "error");
  assert.equal(failed.completed, 2);
  assert.equal(failed.label, "本次规划未完成");
  assert.equal(getPlanningProgress([], "complete").label, "旅行计划已保存");
});
