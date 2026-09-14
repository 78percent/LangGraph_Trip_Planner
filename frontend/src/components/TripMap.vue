<script setup lang="ts">
import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
  watch,
} from "vue";
import AMapLoader from "@amap/amap-jsapi-loader";
import { errorMessage, queryRoute } from "@/services/api";
import type { Attraction, RouteInfo } from "@/types";

const props = defineProps<{ points: Attraction[]; city: string }>();
const container = ref<HTMLDivElement | null>(null);
const error = ref("");
const loading = ref(false);
const start = ref(0);
const mode = ref("walking");
const route = ref<RouteInfo | null>(null);
const pairs = computed(() => props.points.slice(0, -1));
// The vendor loader returns a runtime SDK with no bundled TypeScript definitions.
let map: any;
let sdk: any;
let line: any;
let disposed = false;
async function initialize() {
  error.value = "";
  if (!import.meta.env.VITE_AMAP_WEB_KEY) {
    error.value = "尚未配置浏览器地图 Key，行程文字仍可正常查看。";
    return;
  }
  try {
    const windowWithMap = window as typeof window & {
      _AMapSecurityConfig?: { securityJsCode: string };
    };
    windowWithMap._AMapSecurityConfig = {
      securityJsCode: import.meta.env.VITE_AMAP_SECURITY_CODE || "",
    };
    sdk = await AMapLoader.load({
      key: import.meta.env.VITE_AMAP_WEB_KEY,
      version: "2.0",
    });
    if (disposed || !container.value) return;
    map = new sdk.Map(container.value, { zoom: 12, viewMode: "2D" });
    drawPoints();
  } catch {
    error.value = "地图加载失败，请检查浏览器地图 Key、域名配置或网络。";
  }
}
function drawPoints() {
  if (!map) return;
  map.clearMap();
  route.value = null;
  line = null;
  start.value = 0;
  props.points.forEach((point, index) => {
    const content = document.createElement("div");
    content.textContent = `${index + 1} · ${point.name}`;
    content.style.cssText =
      "background:#286557;color:white;padding:5px 9px;border-radius:6px;white-space:nowrap;font-size:12px";
    map.add(
      new sdk.Marker({
        position: [point.location.longitude, point.location.latitude],
        content,
      }),
    );
  });
  if (props.points.length) map.setFitView(null, false, [50, 50, 50, 50]);
}
async function loadRoute() {
  const origin = props.points[start.value];
  const destination = props.points[start.value + 1];
  if (!origin || !destination) return;
  loading.value = true;
  error.value = "";
  route.value = null;
  if (line && map) map.remove(line);
  try {
    route.value = await queryRoute(
      origin.location,
      destination.location,
      props.city,
      mode.value,
    );
    if (map && route.value.polyline.length) {
      line = new sdk.Polyline({
        path: route.value.polyline,
        strokeColor: "#cf8650",
        strokeWeight: 6,
      });
      map.add(line);
      map.setFitView([line]);
    }
  } catch (e) {
    error.value = errorMessage(e);
  } finally {
    loading.value = false;
  }
}
watch(
  () => props.points,
  async () => {
    await nextTick();
    drawPoints();
  },
);
onMounted(initialize);
onBeforeUnmount(() => {
  disposed = true;
  map?.destroy();
});
</script>

<template>
  <div
    ref="container"
    style="height: 360px; border-radius: 12px; background: #e9eee5"
  ></div>
  <p class="muted">标记使用高德实际坐标。选择一段相邻景点，查询真实路线。</p>
  <div v-if="pairs.length" class="grid">
    <label class="field"
      ><span>路线</span
      ><select v-model.number="start" :disabled="loading">
        <option v-for="(point, index) in pairs" :key="index" :value="index">
          {{ point.name }} → {{ points[index + 1]?.name }}
        </option>
      </select></label
    ><label class="field"
      ><span>交通</span
      ><select v-model="mode" :disabled="loading">
        <option value="walking">步行</option>
        <option value="driving">驾车</option>
        <option value="transit">公共交通</option>
      </select></label
    >
  </div>
  <a-button v-if="pairs.length" :loading="loading" @click="loadRoute"
    >查询这段路线</a-button
  >
  <p v-if="route">
    约 {{ (route.distance / 1000).toFixed(1) }} 公里 ·
    {{ Math.ceil(route.duration / 60) }} 分钟
  </p>
  <div v-if="error" role="alert" class="notice">{{ error }}</div>
</template>
