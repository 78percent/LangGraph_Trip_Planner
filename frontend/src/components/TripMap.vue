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
const mapError = ref("");
const mapLoading = ref(false);
const loading = ref(false);
const start = ref(0);
const mode = ref("walking");
const route = ref<RouteInfo | null>(null);
const pairs = computed(() => props.points.slice(0, -1));
const mapLink = computed(() => {
  const point = props.points[0];
  const url = new URL(`https://uri.amap.com/${point ? "marker" : "search"}`);
  if (point) {
    url.searchParams.set(
      "position",
      `${point.location.longitude},${point.location.latitude}`,
    );
    url.searchParams.set("name", point.name);
    url.searchParams.set("coordinate", "gaode");
  } else {
    url.searchParams.set("keyword", props.city);
    url.searchParams.set("city", props.city);
  }
  url.searchParams.set("src", "LangGraphTripPlanner");
  url.searchParams.set("callnative", "0");
  return url.href;
});
// The vendor loader returns a runtime SDK with no bundled TypeScript definitions.
let map: any;
let sdk: any;
let line: any;
let disposed = false;
let attempt = 0;
let mapTimeout: ReturnType<typeof setTimeout> | undefined;
async function initialize() {
  const currentAttempt = ++attempt;
  clearTimeout(mapTimeout);
  map?.destroy();
  map = null;
  line = null;
  mapError.value = "";
  mapLoading.value = false;
  if (!import.meta.env.VITE_AMAP_WEB_KEY) {
    mapError.value = "尚未配置浏览器地图 Key，可先在高德打开景点。";
    return;
  }
  mapLoading.value = true;
  mapTimeout = setTimeout(() => {
    if (disposed || currentAttempt !== attempt) return;
    mapLoading.value = false;
    mapError.value =
      "地图加载超时，请检查网络或浏览器地图 Key 的域名白名单后重试。";
  }, 12000);
  try {
    const windowWithMap = window as typeof window & {
      _AMapSecurityConfig?: { securityJsCode: string };
    };
    windowWithMap._AMapSecurityConfig = {
      securityJsCode: import.meta.env.VITE_AMAP_SECURITY_CODE || "",
    };
    // A failed script request is cached by the vendor loader until reset.
    if (!sdk) {
      // Version 1.0.1 implements reset but omits it from its type declarations.
      (AMapLoader as typeof AMapLoader & { reset: () => void }).reset();
    }
    sdk = await AMapLoader.load({
      key: import.meta.env.VITE_AMAP_WEB_KEY,
      version: "2.0",
    });
    if (disposed || currentAttempt !== attempt || !container.value) return;
    map = new sdk.Map(container.value, { zoom: 12, viewMode: "2D" });
    // `complete` only ends the loading wait: tile auth failures can emit it too.
    map.on("complete", () => {
      if (disposed || currentAttempt !== attempt) return;
      clearTimeout(mapTimeout);
      mapLoading.value = false;
      mapError.value = "";
    });
    drawPoints();
  } catch {
    if (disposed || currentAttempt !== attempt) return;
    clearTimeout(mapTimeout);
    mapLoading.value = false;
    mapError.value =
      "地图加载失败，请检查浏览器地图 Key、域名白名单或网络后重试。";
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
  clearTimeout(mapTimeout);
  map?.destroy();
});
</script>

<template>
  <div
    ref="container"
    style="height: 360px; border-radius: 12px; background: #e9eee5"
  ></div>
  <div class="map-actions">
    <a-button :loading="mapLoading" @click="initialize">重新加载地图</a-button>
    <a :href="mapLink" target="_blank" rel="noopener noreferrer">在高德打开</a>
  </div>
  <div v-if="mapError" role="alert" class="notice">{{ mapError }}</div>
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

<style scoped>
.map-actions {
  display: flex;
  align-items: center;
  gap: 16px;
  margin: 12px 0 20px;
}
</style>
