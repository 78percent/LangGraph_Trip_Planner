<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import TripMap from "@/components/TripMap.vue";
import AppIcon from "@/components/AppIcon.vue";
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
const suggestions = computed(() => {
  const paragraphs = (plan.value?.overall_suggestions || "")
    .replace(/\\n/g, "\n")
    .replace(/([。！？；.!?;])\s*(?=\d+[)）])/g, "$1\n")
    .split(/\n+/)
    .map((paragraph) => paragraph.trim())
    .filter(Boolean);
  const first = paragraphs[0] || "";
  const hasIntro = first.length <= 160 && !/^\d+[)）]/.test(first);
  return {
    intro: hasIntro ? first : "",
    advice: hasIntro ? paragraphs.slice(1) : paragraphs,
  };
});
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
      backgroundColor: "#f7f8f2",
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
  <div class="result-page">
    <div v-if="loading" class="panel" role="status">正在读取旅行计划…</div>
    <div v-if="error" role="alert" class="error">{{ error }}</div>
    <div class="result-toolbar">
      <RouterLink to="/" class="back-link">← 返回我的旅行</RouterLink>
      <div v-if="plan" class="actions export-actions">
        <a-button :loading="exporting" @click="exportPlan('png')"
          >导出图片</a-button
        >
        <a-button :loading="exporting" @click="exportPlan('pdf')"
          >导出 PDF</a-button
        >
      </div>
    </div>
    <template v-if="plan">
      <div ref="printable" class="itinerary travel-journal">
        <header class="journal-cover">
          <div class="journal-title">
            <div>
              <p class="journal-dates">
                <AppIcon name="calendar" :size="17" />
                <span>{{ plan.start_date }} — {{ plan.end_date }}</span>
                <span class="trip-length">{{ plan.days.length }} 天</span>
              </p>
              <h1>{{ plan.city }}，慢慢走。</h1>
            </div>
            <AppIcon name="compass" :size="68" class="journal-compass" />
          </div>
          <p v-if="suggestions.intro" class="journal-intro">
            {{ suggestions.intro }}
          </p>
        </header>

        <nav
          class="day-navigation"
          aria-label="行程日期"
          data-html2canvas-ignore
        >
          <a
            v-for="(day, index) in plan.days"
            :key="day.date"
            :href="`#day-${index + 1}`"
          >
            第 {{ index + 1 }} 天
            <span>{{ day.date.slice(5).replace("-", "/") }}</span>
          </a>
          <a href="#trip-map" class="map-jump"
            ><AppIcon name="pin" :size="16" />路线地图</a
          >
        </nav>

        <div v-if="plan.warnings.length" class="journal-warnings">
          <p v-for="warning in plan.warnings" :key="warning">{{ warning }}</p>
        </div>

        <div class="journal-layout">
          <div class="journal-days">
            <section
              v-for="(day, index) in plan.days"
              :id="`day-${index + 1}`"
              :key="day.date"
              class="journal-day"
              :aria-labelledby="`day-title-${index + 1}`"
            >
              <header class="journal-day-heading">
                <h2 :id="`day-title-${index + 1}`">
                  第 <span>{{ String(index + 1).padStart(2, "0") }}</span> 天
                </h2>
                <time :datetime="day.date">{{ day.date }}</time>
              </header>
              <p class="day-intro">{{ day.description }}</p>
              <div class="day-transport">
                <AppIcon name="route" :size="17" />
                <span>{{ day.transportation }}</span>
                <span class="transport-cost"
                  >交通约 ¥{{ day.transportation_cost }}</span
                >
              </div>

              <ol class="attraction-list">
                <li
                  v-for="(point, pointIndex) in day.attractions"
                  :key="point.poi_id || pointIndex"
                  class="attraction-item"
                >
                  <span class="attraction-number" aria-hidden="true">{{
                    String(pointIndex + 1).padStart(2, "0")
                  }}</span>
                  <article class="attraction-content">
                    <h3>{{ point.name }}</h3>
                    <p class="attraction-description">
                      {{ point.description }}
                    </p>
                    <div class="attraction-facts">
                      <span>建议 {{ point.visit_duration }} 分钟</span>
                      <span>门票约 ¥{{ point.ticket_price }}</span>
                    </div>
                    <p v-if="point.address" class="attraction-address">
                      <AppIcon name="pin" :size="14" />{{ point.address }}
                    </p>
                  </article>
                </li>
              </ol>

              <div v-if="day.hotel || day.meals.length" class="day-living">
                <section v-if="day.hotel" class="stay-details">
                  <h3>今晚住这里</h3>
                  <div class="living-title">
                    <strong>{{ day.hotel.name }}</strong
                    ><span>约 ¥{{ day.hotel.estimated_cost }} / 晚</span>
                  </div>
                  <p>{{ day.hotel.address }}</p>
                </section>
                <section v-if="day.meals.length" class="meal-details">
                  <h3>三餐安排</h3>
                  <div
                    v-for="meal in day.meals"
                    :key="meal.type"
                    class="meal-row"
                  >
                    <span class="meal-type">{{ mealNames[meal.type] }}</span>
                    <div class="meal-copy">
                      <div class="living-title">
                        <strong>{{ meal.name }}</strong
                        ><span>约 ¥{{ meal.estimated_cost }}</span>
                      </div>
                      <p>{{ meal.description }}</p>
                    </div>
                  </div>
                </section>
              </div>
            </section>
          </div>

          <aside class="journal-sidebar" aria-label="旅行参考">
            <section class="budget-summary">
              <h2>旅行预算</h2>
              <div class="budget-total">
                <span>¥</span>{{ plan.budget.total.toLocaleString() }}
              </div>
              <p class="budget-caption">预计总花费</p>
              <dl class="budget-breakdown">
                <div>
                  <dt>景点门票</dt>
                  <dd>¥{{ plan.budget.total_attractions.toLocaleString() }}</dd>
                </div>
                <div>
                  <dt>住宿</dt>
                  <dd>¥{{ plan.budget.total_hotels.toLocaleString() }}</dd>
                </div>
                <div>
                  <dt>餐饮</dt>
                  <dd>¥{{ plan.budget.total_meals.toLocaleString() }}</dd>
                </div>
                <div>
                  <dt>交通</dt>
                  <dd>
                    ¥{{ plan.budget.total_transportation.toLocaleString() }}
                  </dd>
                </div>
              </dl>
              <p v-if="plan.budget.note" class="budget-note">
                {{ plan.budget.note }}
              </p>
            </section>
            <section v-if="plan.weather_info.length" class="weather-summary">
              <h2>天气预报</h2>
              <div
                v-for="item in plan.weather_info"
                :key="item.date"
                class="weather-day"
              >
                <div class="weather-date">
                  <time :datetime="item.date">{{
                    item.date.slice(5).replace("-", "/")
                  }}</time
                  ><strong>{{ item.day_temp ?? "未知" }}°C</strong>
                </div>
                <p>{{ item.day_weather }}</p>
                <p class="weather-night">
                  夜间 {{ item.night_weather }} ·
                  {{ item.night_temp ?? "未知" }}°C
                </p>
              </div>
            </section>
          </aside>
        </div>
        <section v-if="suggestions.advice.length" class="journal-advice">
          <h2>出行建议</h2>
          <p v-for="(paragraph, index) in suggestions.advice" :key="index">
            {{ paragraph }}
          </p>
        </section>
        <p class="journal-source">{{ plan.source }}</p>
      </div>

      <section id="trip-map" class="journal-map">
        <div class="map-heading">
          <h2>沿着地图出发</h2>
          <label class="map-date">
            <span class="sr-only">选择地图日期</span>
            <select v-model.number="dayIndex">
              <option
                v-for="(day, index) in plan.days"
                :key="day.date"
                :value="index"
              >
                第 {{ index + 1 }} 天 · {{ day.date }}
              </option>
            </select>
          </label>
        </div>
        <TripMap :points="points" :city="plan.city" />
      </section>

      <form class="revision-form" @submit.prevent="revise">
        <div class="revision-heading">
          <h2>让行程更合心意</h2>
          <p>调整后另存为新计划，城市与日期保持不变。</p>
        </div>
        <div class="revision-input">
          <label class="field">
            <span>修改要求</span>
            <textarea
              v-model="instruction"
              rows="3"
              maxlength="2000"
              placeholder="例如：第二天只安排一个景点，节奏轻松一些。"
              :disabled="revising"
            ></textarea>
          </label>
          <a-button
            type="primary"
            html-type="submit"
            :loading="revising"
            :disabled="!instruction.trim()"
            >生成调整后的计划</a-button
          >
        </div>
      </form>
      <p class="export-note">图片与 PDF 包含完整文字行程，不含交互地图。</p>
    </template>
  </div>
</template>

<style scoped>
.result-page {
  min-width: 0;
}
.result-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin: -12px 0 24px;
}
.export-actions {
  gap: 8px;
}
.travel-journal {
  overflow-wrap: anywhere;
}
.journal-cover {
  padding: 34px 0 36px;
  border-top: 1px solid var(--line);
}
.journal-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}
.journal-title h1 {
  margin: 17px 0 20px;
  font-size: clamp(36px, 4vw, 52px);
  letter-spacing: 2px;
}
.journal-dates {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: var(--muted);
}
.trip-length {
  margin-left: 8px;
  padding-left: 16px;
  border-left: 1px solid #bec9b9;
  color: var(--green);
}
.journal-compass {
  flex-shrink: 0;
  color: #8c9e7b;
  margin-right: 22px;
}
.journal-intro {
  max-width: 78ch;
  font-size: 15px;
  line-height: 2;
  color: #5a695b;
  white-space: pre-line;
}
.day-navigation {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px 10px;
  padding: 13px 0;
  border-top: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
  margin-bottom: 38px;
}
.day-navigation a {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 11px;
  min-height: 44px;
  padding: 10px 14px;
  border-radius: 6px;
  color: var(--ink);
  font-size: 14px;
}
.day-navigation a span {
  font-size: 12px;
  color: var(--muted);
}
.day-navigation a:hover {
  background: #e9eee2;
}
.day-navigation .map-jump {
  margin-left: auto;
  color: var(--green);
}
.journal-warnings {
  margin: -12px 0 32px;
  padding: 4px 0 4px 16px;
  border-left: 2px solid #cbb777;
  color: #796735;
  font-size: 13px;
}
.journal-warnings p + p {
  margin-top: 7px;
}
.journal-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 280px;
  gap: clamp(32px, 5vw, 70px);
  align-items: start;
}
.journal-days,
.journal-sidebar {
  min-width: 0;
}
.journal-day {
  scroll-margin-top: 28px;
  padding-bottom: 38px;
  margin-bottom: 38px;
  border-bottom: 1px solid var(--line);
}
.journal-day:last-child {
  margin-bottom: 0;
}
.journal-day-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 21px;
}
.journal-day-heading h2 {
  font-family: var(--serif);
  font-size: 23px;
  font-weight: 500;
  margin: 0;
}
.journal-day-heading h2 span {
  font-family: Georgia, serif;
  font-size: 34px;
  margin: 0 5px;
}
.journal-day-heading time {
  color: var(--muted);
  font-size: 13px;
  font-variant-numeric: tabular-nums;
}
.day-intro {
  font-size: 15px;
  line-height: 2;
  color: #596758;
  white-space: pre-line;
}
.day-transport {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  gap: 5px 9px;
  padding: 14px 0 23px;
  color: #697560;
  font-size: 12px;
  line-height: 1.7;
}
.day-transport .app-icon {
  margin-top: 2px;
}
.day-transport > span:first-of-type {
  flex: 1;
  min-width: 130px;
}
.transport-cost {
  white-space: nowrap;
}
.attraction-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.attraction-item {
  display: grid;
  grid-template-columns: 28px minmax(0, 1fr);
  gap: 16px;
  padding: 26px 0;
  border-top: 1px solid var(--line);
}
.attraction-number {
  font-family: Georgia, serif;
  font-size: 19px;
  line-height: 1.5;
  color: #82936d;
}
.attraction-content h3 {
  font-size: 19px;
  font-weight: 600;
  line-height: 1.5;
  margin: 0 0 11px;
}
.attraction-description {
  font-size: 15px;
  line-height: 1.95;
  color: #465748;
  white-space: pre-line;
}
.attraction-facts {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 7px 20px;
  margin-top: 14px;
  font-size: 12px;
  color: #53664c;
}
.attraction-facts span + span {
  padding-left: 19px;
  border-left: 1px solid #d1d9c8;
}
.attraction-address {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin-top: 8px;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.8;
}
.attraction-address .app-icon {
  margin-top: 3px;
}
.day-living {
  background: #eff2e8;
  border-radius: 10px;
  padding: 25px 26px;
  margin-top: 3px;
}
.day-living h3 {
  font-size: 13px;
  font-weight: 500;
  color: #69785d;
  margin-bottom: 14px;
}
.stay-details + .meal-details {
  border-top: 1px solid #d9e0cf;
  margin-top: 22px;
  padding-top: 22px;
}
.living-title {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 4px 14px;
  line-height: 1.7;
}
.living-title strong {
  font-size: 14px;
  font-weight: 500;
}
.living-title > span {
  color: #69785d;
  font-size: 12px;
  white-space: nowrap;
}
.day-living p {
  color: #677360;
  font-size: 13px;
  line-height: 1.85;
  margin-top: 5px;
}
.meal-row {
  display: grid;
  grid-template-columns: 30px minmax(0, 1fr);
  gap: 15px;
}
.meal-row + .meal-row {
  margin-top: 18px;
}
.meal-type {
  font-size: 12px;
  line-height: 2;
  color: #728164;
}
.journal-sidebar {
  border-left: 1px solid var(--line);
  padding-left: 28px;
}
.journal-sidebar h2 {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 20px;
}
.budget-total {
  font-family: Georgia, serif;
  font-size: 41px;
  color: var(--green);
  line-height: 1.2;
  font-variant-numeric: tabular-nums;
}
.budget-total > span {
  font-size: 23px;
  margin-right: 5px;
}
.budget-caption {
  font-size: 12px;
  color: var(--muted);
  margin-top: 5px;
}
.budget-breakdown {
  margin: 23px 0 0;
  padding: 20px 0;
  border-top: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
}
.budget-breakdown > div {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 15px;
  font-size: 13px;
}
.budget-breakdown > div + div {
  margin-top: 15px;
}
.budget-breakdown dt {
  color: #677360;
}
.budget-breakdown dd {
  margin: 0;
  font-variant-numeric: tabular-nums;
}
.budget-note {
  color: var(--muted);
  font-size: 12px;
  line-height: 1.9;
  margin-top: 17px;
}
.weather-summary {
  margin-top: 39px;
  padding-top: 27px;
  border-top: 1px solid var(--line);
}
.weather-day + .weather-day {
  margin-top: 19px;
  padding-top: 19px;
  border-top: 1px solid var(--line);
}
.weather-date {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.weather-date time {
  font-size: 13px;
}
.weather-date strong {
  font-size: 18px;
  font-weight: 500;
}
.weather-day > p {
  font-size: 13px;
  margin-top: 5px;
}
.weather-day .weather-night {
  font-size: 12px;
  color: var(--muted);
}
.journal-advice {
  max-width: 78ch;
  padding-top: 32px;
}
.journal-advice h2 {
  font-size: 18px;
  margin-bottom: 14px;
}
.journal-advice p {
  color: #596758;
  font-size: 14px;
  line-height: 2;
}
.journal-advice p + p {
  margin-top: 14px;
}
.journal-source {
  font-size: 12px;
  color: var(--muted);
  margin: 23px 0 35px;
}
.journal-map {
  scroll-margin-top: 24px;
  padding: 28px;
  border: 1px solid var(--line);
  background: var(--surface);
  border-radius: 14px;
  margin-bottom: 35px;
}
.map-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 22px;
}
.map-heading h2 {
  margin: 0;
  font-size: 21px;
  font-family: var(--serif);
}
.map-date {
  min-width: 225px;
}
.map-date select {
  background: #f7f8f2;
}
.revision-form {
  display: grid;
  grid-template-columns: minmax(0, 0.75fr) minmax(0, 1fr);
  gap: 45px;
  padding: 34px 0;
  border-top: 1px solid var(--line);
}
.revision-heading h2 {
  font-family: var(--serif);
  font-size: 24px;
  margin: 0 0 12px;
}
.revision-heading p {
  color: var(--muted);
  font-size: 13px;
  max-width: 30em;
}
.revision-input .field {
  margin-bottom: 15px;
}
.export-note {
  color: var(--muted);
  font-size: 12px;
  margin-top: 6px;
}
@media (max-width: 1023px) {
  .journal-layout {
    grid-template-columns: minmax(0, 1fr) 230px;
    gap: 30px;
  }
  .journal-sidebar {
    padding-left: 23px;
  }
  .day-living {
    padding: 22px;
  }
  .attraction-item {
    gap: 11px;
  }
}
@media (max-width: 760px) {
  .journal-layout {
    display: flex;
    flex-direction: column;
    gap: 32px;
  }
  .journal-days {
    width: 100%;
  }
  .journal-sidebar {
    width: 100%;
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
    gap: 30px;
    padding: 0;
    border: 0;
  }
  .weather-summary {
    margin: 0;
    padding: 0;
    border: 0;
  }
  .journal-compass {
    width: 52px;
    height: 52px;
    margin: 0;
  }
  .journal-intro,
  .day-intro,
  .attraction-description {
    font-size: 16px;
  }
  .revision-form {
    grid-template-columns: 1fr;
    gap: 24px;
  }
}
@media (max-width: 480px) {
  .result-toolbar {
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 18px;
  }
  .export-actions .ant-btn {
    padding: 0 11px;
  }
  .journal-cover {
    padding: 27px 0;
  }
  .journal-dates {
    gap: 8px;
    font-size: 12px;
  }
  .trip-length {
    margin: 0;
    padding-left: 9px;
  }
  .journal-title {
    gap: 10px;
  }
  .journal-title h1 {
    font-size: 34px;
    letter-spacing: 0;
    margin: 18px 0;
  }
  .journal-compass {
    display: none;
  }
  .day-navigation {
    gap: 3px;
    margin-bottom: 28px;
  }
  .day-navigation a {
    padding: 9px 11px;
    gap: 8px;
    font-size: 13px;
  }
  .day-navigation .map-jump {
    margin-left: 0;
  }
  .journal-day-heading h2 {
    font-size: 21px;
  }
  .journal-day-heading h2 span {
    font-size: 30px;
  }
  .journal-day-heading time {
    font-size: 12px;
  }
  .day-transport {
    gap: 6px;
  }
  .attraction-item {
    grid-template-columns: 22px minmax(0, 1fr);
    gap: 10px;
    padding: 23px 0;
  }
  .attraction-number {
    font-size: 16px;
  }
  .attraction-content h3 {
    font-size: 18px;
  }
  .day-living {
    padding: 21px 18px;
  }
  .meal-row {
    gap: 10px;
  }
  .journal-sidebar {
    grid-template-columns: 1fr;
    gap: 30px;
  }
  .weather-summary {
    padding-top: 25px;
    border-top: 1px solid var(--line);
  }
  .journal-map {
    padding: 20px 16px;
  }
  .map-date {
    width: 100%;
    min-width: 0;
  }
}
</style>
