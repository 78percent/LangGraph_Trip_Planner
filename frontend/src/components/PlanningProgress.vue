<script setup lang="ts">
import { computed } from "vue";
import { getPlanningProgress, type PlanningStatus } from "./planningProgress";
import AppIcon from "./AppIcon.vue";

const props = defineProps<{ messages: string[]; status: PlanningStatus }>();
const progress = computed(() =>
  getPlanningProgress(props.messages, props.status),
);
const stages = ["查询资料", "编排行程", "核对行程", "保存计划"];
</script>

<template>
  <section
    class="planning-progress"
    :class="status"
    aria-label="旅行规划进度"
    :aria-busy="status === 'running'"
  >
    <div class="progress-heading">
      <span class="progress-emblem"
        ><AppIcon :name="status === 'error' ? 'compass' : 'route'" :size="23"
      /></span>
      <div class="progress-heading-text">
        <strong role="status">{{ progress.label }}</strong
        ><span>{{ progress.completed }} / 4 个阶段已完成</span>
      </div>
    </div>
    <div
      class="stage-track"
      role="progressbar"
      aria-label="已完成的规划阶段"
      aria-valuemin="0"
      aria-valuemax="4"
      :aria-valuenow="progress.completed"
      :aria-valuetext="`${progress.label}，${progress.completed} / 4 个阶段已完成`"
    >
      <span
        class="stage-fill"
        :style="{ transform: `scaleX(${progress.completed / 4})` }"
      ></span>
      <span
        v-if="status === 'running' && progress.completed < 4"
        class="stage-current"
        :style="{ left: `${progress.completed * 25}%` }"
      ></span>
    </div>
    <ol class="stage-labels">
      <li
        v-for="(stage, index) in stages"
        :key="stage"
        :class="{
          done: index < progress.completed,
          current: status === 'running' && index === progress.completed,
        }"
        :aria-current="
          status === 'running' && index === progress.completed
            ? 'step'
            : undefined
        "
      >
        <span class="stage-dot">{{
          index < progress.completed ? "✓" : index + 1
        }}</span
        >{{ stage }}
      </li>
    </ol>
    <details v-if="messages.length" class="progress-details">
      <summary>查看运行记录</summary>
      <ol>
        <li v-for="(message, index) in messages" :key="index">{{ message }}</li>
      </ol>
    </details>
  </section>
</template>

<style scoped>
.planning-progress {
  margin-top: 24px;
  padding: 22px;
  border: 1px solid #d5e1cb;
  background: #f0f4e9;
  border-radius: 14px;
}
.progress-heading {
  display: flex;
  align-items: center;
  gap: 13px;
  margin-bottom: 22px;
}
.progress-emblem {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  background: #e1e9d6;
  border-radius: 50%;
  color: var(--green);
  flex-shrink: 0;
}
.progress-heading-text {
  display: grid;
  gap: 5px;
  min-width: 0;
}
.progress-heading strong {
  font-size: 14px;
  font-weight: 550;
  line-height: 1.6;
}
.progress-heading-text > span {
  color: #697760;
  font-size: 12px;
}
.stage-track {
  height: 6px;
  position: relative;
  background: #dde5d4;
  overflow: hidden;
  border-radius: 8px;
}
.stage-fill {
  position: absolute;
  inset: 0;
  background: var(--green);
  transform-origin: left;
  transition: transform 0.65s ease;
  border-radius: inherit;
}
.stage-current {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 25%;
  background: #a9bd95;
  overflow: hidden;
  transition: left 0.65s ease;
}
.stage-current::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, #f3f7e9b3, transparent);
  animation: progress-shimmer 1.9s ease-in-out infinite;
}
@keyframes progress-shimmer {
  from {
    transform: translateX(-100%);
  }
  to {
    transform: translateX(100%);
  }
}
.stage-labels {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 7px;
  padding: 0;
  margin: 17px 0 0;
  list-style: none;
}
.stage-labels li {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: #76816b;
  white-space: nowrap;
}
.stage-labels .done,
.stage-labels .current {
  color: #335a35;
}
.stage-labels .current {
  font-weight: 600;
}
.stage-dot {
  width: 18px;
  height: 18px;
  display: grid;
  place-items: center;
  font-size: 10px;
  border: 1px solid #c3cfb6;
  border-radius: 50%;
  flex-shrink: 0;
}
.done .stage-dot {
  background: var(--green);
  border-color: var(--green);
  color: white;
}
.current .stage-dot {
  border-color: var(--green);
}
.progress-details {
  margin-top: 18px;
  border-top: 1px solid #dbe3d1;
  padding-top: 10px;
  font-size: 12px;
  color: #64715a;
}
.progress-details summary {
  cursor: pointer;
  padding: 5px 0;
}
.progress-details ol {
  padding-left: 20px;
  margin: 8px 0 0;
  line-height: 1.9;
}
.error {
  color: inherit;
  border-color: #ead3c8;
  background: #fcf3ed;
}
.error .progress-emblem {
  background: #f3e4d9;
  color: #9c6550;
}
.error .stage-fill {
  background: #a37e65;
}
@media (max-width: 580px) {
  .planning-progress {
    padding: 18px 15px;
  }
  .progress-heading {
    gap: 10px;
  }
  .progress-heading strong {
    font-size: 13px;
  }
  .stage-labels li {
    flex-direction: column;
    gap: 7px;
    font-size: 11px;
  }
}
@media (prefers-reduced-motion: reduce) {
  .stage-fill,
  .stage-current {
    transition: none;
  }
  .stage-current::after {
    animation: none;
  }
}
</style>
