<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import TripMap from "@/components/TripMap.vue";
import { errorMessage, getPlan, revisePlan } from "@/services/api";
import type { TripPlan } from "@/types";

const route = useRoute();
const router = useRouter();
const plan = ref<TripPlan | null>(null);
const error = ref("");
const loading = ref(false);
const revising = ref(false);
const exporting = ref(false);
const instruction = ref("");
const dayIndex = ref(0);
const printable = ref<HTMLElement | null>(null);
const points = computed(
  () => plan.value?.days[dayIndex.value]?.attractions || [],
);
const mealNames = { breakfast: "早餐", lunch: "午餐", dinner: "晚餐" };
watch(
  () => route.query.id,
  async (id) => {
    plan.value = null;
    error.value = "";
    loading.value = true;
    dayIndex.value = 0;
    try {
      if (typeof id !== "string") throw new Error("请先生成或选择一份行程。");
      plan.value = await getPlan(id);
    } catch (e) {
      error.value = errorMessage(e);
    } finally {
      loading.value = false;
    }
  },
  { immediate: true },
);
async function revise() {
  if (!plan.value || !instruction.value.trim()) return;
  revising.value = true;
  error.value = "";
  try {
    const updated = await revisePlan(plan.value.id, instruction.value);
    instruction.value = "";
    await router.push({ path: "/result", query: { id: updated.id } });
  } catch (e) {
    error.value = errorMessage(e);
  } finally {
    revising.value = false;
  }
}
async function exportPlan(format: "png" | "pdf") {
  if (!printable.value || !plan.value) return;
  exporting.value = true;
  error.value = "";
  try {
    const { default: html2canvas } = await import("html2canvas");
    const canvas = await html2canvas(printable.value, {
      scale: 1.5,
      backgroundColor: "#f6f5f0",
      useCORS: true,
    });
    const filename = `${plan.value.city}-${plan.value.start_date}`;
    if (format === "png") {
      const link = document.createElement("a");
      link.download = `${filename}.png`;
      link.href = canvas.toDataURL("image/png");
      link.click();
    } else {
      const { default: jsPDF } = await import("jspdf");
      const pdf = new jsPDF("p", "mm", "a4");
      const width = 190;
      const sliceHeight = Math.floor((canvas.width * 277) / width);
      for (let top = 0; top < canvas.height; top += sliceHeight) {
        const slice = document.createElement("canvas");
        slice.width = canvas.width;
        slice.height = Math.min(sliceHeight, canvas.height - top);
        slice
          .getContext("2d")!
          .drawImage(
            canvas,
            0,
            top,
            canvas.width,
            slice.height,
            0,
            0,
            slice.width,
            slice.height,
          );
        if (top > 0) pdf.addPage();
        pdf.addImage(
          slice.toDataURL("image/png"),
          "PNG",
          10,
          10,
          width,
          (slice.height * width) / slice.width,
        );
      }
      pdf.save(`${filename}.pdf`);
    }
  } catch {
    error.value = "导出失败，行程仍已保存在历史记录中。";
  } finally {
    exporting.value = false;
  }
}
</script>

<template>
  <div v-if="loading" class="panel">正在读取旅行计划…</div>
  <div v-if="error" role="alert" class="error">{{ error }}</div>
  <RouterLink to="/">← 返回规划与历史记录</RouterLink>
  <template v-if="plan">
    <div class="actions" style="margin: 22px 0">
      <a-button :loading="exporting" @click="exportPlan('png')"
        >导出图片</a-button
      ><a-button :loading="exporting" @click="exportPlan('pdf')"
        >导出 PDF</a-button
      ><span class="muted">导出包含文字行程，不含交互地图。</span>
    </div>
    <div ref="printable">
      <section class="hero">
        <div class="eyebrow">YOUR JOURNEY, DAY BY DAY.</div>
        <h1>{{ plan.city }}，慢慢走。</h1>
        <p>
          {{ plan.start_date }} — {{ plan.end_date }} ·
          {{ plan.days.length }} 天
        </p>
        <p class="muted">{{ plan.overall_suggestions }}</p>
      </section>
      <div v-for="warning in plan.warnings" :key="warning" class="notice">
        {{ warning }}
      </div>
      <section class="panel">
        <h2>预算概览</h2>
        <div class="cost-grid">
          <div>
            <span class="muted">景点</span
            ><strong>¥{{ plan.budget.total_attractions }}</strong>
          </div>
          <div>
            <span class="muted">住宿</span
            ><strong>¥{{ plan.budget.total_hotels }}</strong>
          </div>
          <div>
            <span class="muted">餐饮</span
            ><strong>¥{{ plan.budget.total_meals }}</strong>
          </div>
          <div>
            <span class="muted">交通</span
            ><strong>¥{{ plan.budget.total_transportation }}</strong>
          </div>
        </div>
        <div class="total">预计合计 ¥{{ plan.budget.total }}</div>
        <p class="muted">{{ plan.budget.note }}</p>
      </section>
      <section v-for="day in plan.days" :key="day.date" class="panel day">
        <div class="eyebrow">DAY {{ day.day_index + 1 }} · {{ day.date }}</div>
        <h2>{{ day.description }}</h2>
        <p class="muted">
          {{ day.transportation }} · 交通估算 ¥{{ day.transportation_cost }}
        </p>
        <article
          v-for="point in day.attractions"
          :key="point.poi_id"
          class="point"
        >
          <h3>{{ point.name }}</h3>
          <p>{{ point.description }}</p>
          <div class="muted">
            {{ point.address }} · 建议 {{ point.visit_duration }} 分钟 ·
            门票估算 ¥{{ point.ticket_price }}
          </div>
        </article>
        <div v-if="day.hotel" class="point">
          <h3>住在 {{ day.hotel.name }}</h3>
          <p class="muted">
            {{ day.hotel.address }} · 每晚估算 ¥{{ day.hotel.estimated_cost }}
          </p>
        </div>
        <div class="point">
          <h3>三餐建议</h3>
          <p v-for="meal in day.meals" :key="meal.type" class="muted">
            {{ mealNames[meal.type] }} · {{ meal.name }} · 估算 ¥{{
              meal.estimated_cost
            }}<br />{{ meal.description }}
          </p>
        </div>
      </section>
      <section v-if="plan.weather_info.length" class="panel">
        <h2>已取得的天气预报</h2>
        <div class="weather-row">
          <div v-for="item in plan.weather_info" :key="item.date">
            <strong>{{ item.date }}</strong>
            <p>{{ item.day_weather }} · {{ item.day_temp ?? "未知" }}°C</p>
            <span class="muted"
              >夜间 {{ item.night_weather }} ·
              {{ item.night_temp ?? "未知" }}°C</span
            >
          </div>
        </div>
      </section>
      <p class="muted">{{ plan.source }}</p>
    </div>
    <section class="panel">
      <h2>在地图上看看</h2>
      <label class="field"
        ><span>选择日期</span
        ><select v-model.number="dayIndex">
          <option
            v-for="(day, index) in plan.days"
            :key="day.date"
            :value="index"
          >
            第 {{ index + 1 }} 天 · {{ day.date }}
          </option>
        </select></label
      ><TripMap :points="points" :city="plan.city" />
    </section>
    <form class="panel" @submit.prevent="revise">
      <h2>再调整一下</h2>
      <p class="muted">
        会重新查询并生成一份新计划，原行程保留。城市与日期保持不变。
      </p>
      <label class="field"
        ><span>修改要求</span
        ><textarea
          v-model="instruction"
          rows="3"
          maxlength="2000"
          placeholder="例如：第二天只安排一个景点，节奏轻松一些。"
          :disabled="revising"
        ></textarea></label
      ><a-button
        type="primary"
        html-type="submit"
        :loading="revising"
        :disabled="!instruction.trim()"
        >生成调整后的计划</a-button
      >
    </form>
  </template>
</template>
