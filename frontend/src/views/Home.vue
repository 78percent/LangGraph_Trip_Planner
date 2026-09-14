<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { errorMessage, generateTripPlan, listPlans } from "@/services/api";
import type { PlanSummary, TripFormData } from "@/types";

const router = useRouter();
const form = reactive<TripFormData>({
  city: "",
  start_date: "",
  end_date: "",
  travel_days: 1,
  transportation: "公共交通",
  accommodation: "经济型酒店",
  preferences: [],
  free_text_input: "",
});
const loading = ref(false);
const error = ref("");
const historyError = ref("");
const progress = ref<string[]>([]);
const plans = ref<PlanSummary[]>([]);
const days = computed(() => {
  if (!form.start_date || !form.end_date) return 0;
  return (
    Math.round(
      (Date.parse(form.end_date) - Date.parse(form.start_date)) / 86400000,
    ) + 1
  );
});
onMounted(async () => {
  try {
    plans.value = await listPlans();
  } catch (e) {
    historyError.value = errorMessage(e);
  }
});
async function submit() {
  error.value = "";
  if (!form.city.trim() || days.value < 1 || days.value > 30) {
    error.value = "请输入城市，并选择 1～30 天的有效日期范围。";
    return;
  }
  loading.value = true;
  progress.value = [];
  try {
    const plan = await generateTripPlan(
      { ...form, travel_days: days.value },
      (text) => progress.value.push(text),
    );
    await router.push({ path: "/result", query: { id: plan.id } });
  } catch (e) {
    error.value = errorMessage(e);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <section class="hero">
    <div class="eyebrow">A LITTLE PLAN. A GREAT JOURNEY.</div>
    <h1>下一站，想去哪里？</h1>
    <p class="muted">告诉我们目的地与偏好，一起安排值得期待的几天。</p>
  </section>
  <form class="panel" @submit.prevent="submit">
    <h2>你的旅行</h2>
    <div class="grid">
      <label class="field"
        ><span>目的地城市</span
        ><input
          v-model="form.city"
          placeholder="例如：杭州"
          maxlength="60"
          required
          :disabled="loading"
      /></label>
      <div class="field">
        <span>行程长度</span>
        <p class="muted">
          {{
            days > 0 ? `${days} 天 · 包含出发与返程当天` : "选择日期后自动计算"
          }}
        </p>
      </div>
      <label class="field"
        ><span>出发日期</span
        ><input
          v-model="form.start_date"
          type="date"
          required
          :disabled="loading"
      /></label>
      <label class="field"
        ><span>返程日期</span
        ><input
          v-model="form.end_date"
          type="date"
          :min="form.start_date"
          required
          :disabled="loading"
      /></label>
      <label class="field"
        ><span>交通方式</span
        ><select v-model="form.transportation" :disabled="loading">
          <option
            v-for="item in ['公共交通', '自驾', '步行', '混合']"
            :key="item"
          >
            {{ item }}
          </option>
        </select></label
      >
      <label class="field"
        ><span>住宿偏好</span
        ><select v-model="form.accommodation" :disabled="loading">
          <option
            v-for="item in ['经济型酒店', '舒适型酒店', '豪华酒店', '民宿']"
            :key="item"
          >
            {{ item }}
          </option>
        </select></label
      >
    </div>
    <div class="field">
      <span>偏爱什么</span>
      <div class="tags">
        <label
          v-for="item in ['历史文化', '自然风光', '美食', '艺术', '休闲']"
          :key="item"
          class="tag"
          ><input
            v-model="form.preferences"
            type="checkbox"
            :value="item"
            :disabled="loading"
          />{{ item }}</label
        >
      </div>
    </div>
    <label class="field"
      ><span>还想告诉我们</span
      ><textarea
        v-model="form.free_text_input"
        rows="3"
        maxlength="2000"
        placeholder="例如：带父母出游，希望每天轻松一些。"
        :disabled="loading"
      ></textarea>
    </label>
    <div class="actions">
      <a-button
        type="primary"
        html-type="submit"
        size="large"
        :loading="loading"
        >{{ loading ? "正在规划…" : "生成旅行计划" }}</a-button
      ><span class="muted">地点来自实际查询，费用为估算。</span>
    </div>
    <div v-if="error" role="alert" class="error">{{ error }}</div>
    <ol v-if="progress.length" class="progress-list" aria-live="polite">
      <li v-for="(item, index) in progress" :key="index">{{ item }}</li>
    </ol>
  </form>
  <section class="panel">
    <h2>保存的旅行</h2>
    <div v-if="historyError" class="error">
      历史记录暂不可用：{{ historyError }}
    </div>
    <p v-else-if="!plans.length" class="muted">
      第一份计划生成后，会保存在这里。
    </p>
    <RouterLink
      v-for="plan in plans"
      :key="plan.id"
      :to="{ path: '/result', query: { id: plan.id } }"
      class="history-item"
      ><strong>{{ plan.city }}</strong
      ><span>{{ plan.start_date }} — {{ plan.end_date }}　→</span></RouterLink
    >
  </section>
</template>
