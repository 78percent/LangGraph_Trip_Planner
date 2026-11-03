<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { errorMessage, generateTripPlan, listPlans } from "@/services/api";
import type { PlanSummary, TripFormData } from "@/types";
import AppIcon from "@/components/AppIcon.vue";
import PlanningProgress from "@/components/PlanningProgress.vue";
import LandscapeCarousel from "@/components/LandscapeCarousel.vue";

const interests = [
  { name: "历史文化", icon: "book" },
  { name: "自然风光", icon: "mountain" },
  { name: "美食", icon: "cup" },
  { name: "艺术", icon: "art" },
  { name: "休闲", icon: "leaf" },
];

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
const planningStatus = ref<"idle" | "running" | "complete" | "error">("idle");
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
  planningStatus.value = "running";
  progress.value = [];
  try {
    const plan = await generateTripPlan(
      { ...form, travel_days: days.value },
      (text) => progress.value.push(text),
    );
    planningStatus.value = "complete";
    await router.push({ path: "/result", query: { id: plan.id } });
  } catch (e) {
    planningStatus.value = "error";
    error.value = errorMessage(e);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="home-layout">
    <section class="travel-cover" aria-labelledby="home-title">
      <div class="cover-copy">
        <span class="cover-kicker"><span></span> 为下一次出发，留一点期待</span>
        <h1 id="home-title">下一站，<br />遇见<em>好风景。</em></h1>
        <p>
          把想去的地方，变成可出发的计划。<br />山野、街巷与远方，都有自己的节奏。
        </p>
      </div>
      <LandscapeCarousel />
      <RouterLink to="/chat" class="cover-chat-link">
        <span class="cover-chat-icon"><AppIcon name="chat" :size="21" /></span>
        <span>还没想好？和途间聊聊</span><AppIcon name="arrow" :size="19" />
      </RouterLink>
    </section>
    <form class="panel planner-panel" @submit.prevent="submit">
      <div class="section-heading planner-heading">
        <h2>规划你的下一程</h2>
        <span v-if="days > 0 && days <= 30" class="duration-badge"
          ><AppIcon name="calendar" :size="15" />{{ days }} 天</span
        >
        <AppIcon v-else name="compass" :size="24" />
      </div>
      <div class="grid form-grid">
        <label class="field city-field"
          ><span>目的地城市</span
          ><input
            v-model="form.city"
            placeholder="想去哪个城市？"
            maxlength="60"
            required
            :disabled="loading"
        /></label>
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
      <fieldset class="field interest-field">
        <legend>旅行偏好</legend>
        <div class="tags">
          <label v-for="item in interests" :key="item.name" class="tag"
            ><input
              v-model="form.preferences"
              type="checkbox"
              :value="item.name"
              :disabled="loading"
            /><AppIcon :name="item.icon" :size="16" />{{ item.name }}</label
          >
        </div>
      </fieldset>
      <label class="field"
        ><span>特别的想法 <span class="optional-label">选填</span></span
        ><textarea
          v-model="form.free_text_input"
          rows="2"
          maxlength="2000"
          placeholder="例如：带父母出游，希望每天轻松一些。"
          :disabled="loading"
        ></textarea>
      </label>
      <div class="planner-submit">
        <a-button
          type="primary"
          html-type="submit"
          size="large"
          class="plan-button"
          :loading="loading"
          >{{ loading ? "正在规划…" : "开启我的旅程"
          }}<AppIcon v-if="!loading" name="arrow" :size="19"
        /></a-button>
        <p class="form-footnote">真实地点 · 费用估算 · 为你安排</p>
      </div>
      <div v-if="error" role="alert" class="error">{{ error }}</div>
      <PlanningProgress
        v-if="planningStatus !== 'idle'"
        :messages="progress"
        :status="planningStatus"
      />
    </form>
  </div>
  <section class="saved-trips" aria-labelledby="saved-title">
    <div class="section-heading">
      <h2 id="saved-title">
        保存的旅行<span v-if="plans.length" class="section-count">{{
          plans.length
        }}</span>
      </h2>
      <AppIcon name="book" :size="22" />
    </div>
    <div v-if="historyError" class="error">
      历史记录暂不可用：{{ historyError }}
    </div>
    <div v-else-if="!plans.length" class="saved-empty">
      <span class="empty-icon"><AppIcon name="route" :size="24" /></span>
      <p>生成的旅行计划会保存在这里。</p>
    </div>
    <div v-if="plans.length" class="saved-grid">
      <RouterLink
        v-for="plan in plans"
        :key="plan.id"
        :to="{ path: '/result', query: { id: plan.id } }"
        class="history-item"
        ><span class="history-icon"><AppIcon name="pin" :size="21" /></span
        ><span class="history-details"
          ><strong>{{ plan.city }}</strong
          ><span>{{ plan.start_date }} — {{ plan.end_date }}</span></span
        ><AppIcon name="arrow" :size="19"
      /></RouterLink>
    </div>
  </section>
</template>
