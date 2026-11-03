<script setup lang="ts">
import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
  useId,
  watch,
} from "vue";
import AppIcon from "./AppIcon.vue";

const scenes = [
  {
    src: "/images/alpine-lake.webp",
    name: "山湖",
    alt: "群山与森林环抱的静谧湖泊",
  },
  {
    src: "/images/forest-light.webp",
    name: "林间",
    alt: "晨光穿过高大树林，洒落在绿色森林里",
  },
  {
    src: "/images/ocean-breeze.webp",
    name: "海岸",
    alt: "开阔海面上的层层波浪与远方天光",
  },
  {
    src: "/images/mountain-dawn.webp",
    name: "远山",
    alt: "日光下绵延的山岭与开阔山谷",
  },
];
const current = ref(0);
const incoming = ref<number | null>(null);
const reveal = ref(0);
const paused = ref(false);
const hovered = ref(false);
const focused = ref(false);
const reducedMotion = ref(false);
const visible = ref(true);
const preparing = ref(false);
const picture = ref<HTMLElement | null>(null);
const viewport = ref({ width: 1000, height: 600 });
const id = useId().replace(/:/g, "");
const filterId = `ink-filter-${id}`;
const maskId = `ink-mask-${id}`;
const scene = computed(() => scenes[current.value]!);
const nextScene = computed(() =>
  incoming.value === null ? null : scenes[incoming.value],
);
const changing = computed(() => preparing.value || incoming.value !== null);
const radius = computed(
  () =>
    Math.pow(reveal.value, 1.35) *
    Math.hypot(viewport.value.width, viewport.value.height) *
    1.3,
);
const failed = new Set<number>();
let timer: ReturnType<typeof setTimeout> | undefined;
let frame = 0;
let disposed = false;
let preference: MediaQueryList | undefined;
let resizeObserver: ResizeObserver | undefined;

function clearTimer() {
  if (timer !== undefined) clearTimeout(timer);
  timer = undefined;
}
function schedule() {
  clearTimer();
  if (
    disposed ||
    paused.value ||
    hovered.value ||
    focused.value ||
    reducedMotion.value ||
    !visible.value ||
    changing.value
  )
    return;
  timer = setTimeout(() => {
    let next = (current.value + 1) % scenes.length;
    while (failed.has(next) && next !== current.value)
      next = (next + 1) % scenes.length;
    if (next !== current.value) void show(next);
  }, 6500);
}
function finish() {
  cancelAnimationFrame(frame);
  if (incoming.value !== null) current.value = incoming.value;
  incoming.value = null;
  reveal.value = 0;
  schedule();
}
async function show(index: number) {
  if (index === current.value || changing.value) return;
  clearTimer();
  preparing.value = true;
  try {
    const image = new Image();
    image.src = scenes[index]!.src;
    await image.decode();
    if (disposed) return;
    failed.delete(index);
    if (reducedMotion.value || !visible.value) {
      current.value = index;
      return;
    }
    incoming.value = index;
    reveal.value = 0;
    await nextTick();
    if (disposed) return;
    const started = performance.now();
    const animate = (now: number) => {
      reveal.value = Math.min(1, (now - started) / 2400);
      if (reveal.value < 1) frame = requestAnimationFrame(animate);
      else finish();
    };
    frame = requestAnimationFrame(animate);
  } catch {
    // Retain the visible photo if a new asset cannot be decoded.
    failed.add(index);
  } finally {
    preparing.value = false;
    schedule();
  }
}
function updatePreference() {
  reducedMotion.value = preference?.matches ?? false;
  if (reducedMotion.value && incoming.value !== null) finish();
}
function updateVisibility() {
  visible.value = !document.hidden;
  if (!visible.value && incoming.value !== null) finish();
}
function onFocusOut(event: FocusEvent) {
  if (
    !(event.currentTarget as HTMLElement).contains(
      event.relatedTarget as Node | null,
    )
  )
    focused.value = false;
}
watch([paused, hovered, focused, reducedMotion, visible], schedule);
onMounted(() => {
  resizeObserver = new ResizeObserver(([entry]) => {
    if (entry)
      viewport.value = {
        width: entry.contentRect.width,
        height: entry.contentRect.height,
      };
  });
  if (picture.value) resizeObserver.observe(picture.value);
  preference = window.matchMedia("(prefers-reduced-motion: reduce)");
  updatePreference();
  updateVisibility();
  preference.addEventListener("change", updatePreference);
  document.addEventListener("visibilitychange", updateVisibility);
  schedule();
});
onBeforeUnmount(() => {
  disposed = true;
  clearTimer();
  cancelAnimationFrame(frame);
  preference?.removeEventListener("change", updatePreference);
  document.removeEventListener("visibilitychange", updateVisibility);
  resizeObserver?.disconnect();
});
</script>

<template>
  <figure
    ref="picture"
    class="cover-image landscape-carousel"
    aria-label="旅行风景"
    aria-roledescription="轮播图"
    @mouseenter="hovered = true"
    @mouseleave="hovered = false"
    @focusin="focused = true"
    @focusout="onFocusOut"
  >
    <img
      :src="scene.src"
      :alt="scene.alt"
      width="1400"
      height="1000"
      fetchpriority="high"
    />
    <svg
      v-if="nextScene"
      class="ink-layer"
      :viewBox="`0 0 ${viewport.width} ${viewport.height}`"
      preserveAspectRatio="none"
      aria-hidden="true"
    >
      <defs>
        <filter
          :id="filterId"
          :x="-viewport.width * 0.25"
          :y="-viewport.height * 0.25"
          :width="viewport.width * 1.5"
          :height="viewport.height * 1.5"
          filterUnits="userSpaceOnUse"
          color-interpolation-filters="sRGB"
        >
          <feTurbulence
            type="fractalNoise"
            baseFrequency="0.012 0.018"
            numOctaves="3"
            seed="7"
            result="grain"
          />
          <feDisplacementMap
            in="SourceGraphic"
            in2="grain"
            :scale="viewport.width * 0.11"
            xChannelSelector="R"
            yChannelSelector="G"
          />
          <feGaussianBlur :stdDeviation="viewport.width * 0.011" />
        </filter>
        <mask
          :id="maskId"
          maskUnits="userSpaceOnUse"
          x="0"
          y="0"
          :width="viewport.width"
          :height="viewport.height"
          style="mask-type: luminance"
        >
          <g :filter="`url(#${filterId})`" fill="white">
            <ellipse
              :cx="viewport.width * 0.325"
              :cy="viewport.height * 0.55"
              :rx="radius"
              :ry="radius * 0.68"
            />
            <ellipse
              :cx="viewport.width * 0.78"
              :cy="viewport.height * 0.25"
              :rx="Math.max(0, radius - viewport.width * 0.15) * 0.68"
              :ry="Math.max(0, radius - viewport.width * 0.15) * 0.8"
            />
            <ellipse
              :cx="viewport.width * 0.08"
              :cy="viewport.height * 0.85"
              :rx="Math.max(0, radius - viewport.width * 0.1) * 0.7"
              :ry="Math.max(0, radius - viewport.width * 0.1) * 0.9"
            />
          </g>
        </mask>
      </defs>
      <image
        :href="nextScene.src"
        x="0"
        y="0"
        :width="viewport.width"
        :height="viewport.height"
        preserveAspectRatio="xMidYMid slice"
        :mask="`url(#${maskId})`"
      />
    </svg>
    <figcaption><span>把时间，留给喜欢的地方。</span></figcaption>
    <div class="landscape-controls" aria-label="风景切换">
      <button
        v-for="(item, index) in scenes"
        :key="item.src"
        type="button"
        class="landscape-dot"
        :aria-label="`切换到${item.name}风景`"
        :aria-pressed="current === index"
        :disabled="changing"
        @click="show(index)"
      >
        <span></span>
      </button>
      <button
        v-if="!reducedMotion"
        type="button"
        class="landscape-pause"
        :aria-label="paused ? '播放风景切换' : '暂停风景切换'"
        :aria-pressed="paused"
        @click="paused = !paused"
      >
        <AppIcon :name="paused ? 'play' : 'pause'" :size="15" />
      </button>
    </div>
  </figure>
</template>

<style scoped>
.landscape-carousel {
  position: relative;
}
.ink-layer {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  pointer-events: none;
}
.landscape-carousel::after {
  z-index: 1;
  pointer-events: none;
}
.landscape-carousel figcaption {
  z-index: 2;
  pointer-events: none;
}
.landscape-controls {
  position: absolute;
  top: 15px;
  right: 17px;
  z-index: 3;
  display: flex;
  align-items: center;
  padding: 0 5px;
  border: 1px solid #ffffff40;
  border-radius: 28px;
  color: #fff;
  background: #19392dd1;
}
.landscape-controls button {
  display: grid;
  place-items: center;
  width: 30px;
  height: 44px;
  padding: 0;
  background: transparent;
  color: inherit;
  border: 0;
  border-radius: 50%;
  cursor: pointer;
}
.landscape-controls button:focus-visible {
  outline-color: #fff;
  outline-offset: -4px;
}
.landscape-controls button:disabled {
  cursor: default;
  opacity: 1;
}
.landscape-dot > span {
  width: 5px;
  height: 5px;
  background: #ffffff70;
  border-radius: 5px;
  transition:
    width 0.25s ease,
    background-color 0.25s ease;
}
.landscape-dot[aria-pressed="true"] > span {
  width: 16px;
  background: #fff;
}
.landscape-controls .landscape-pause {
  width: 37px;
  margin-left: 3px;
  position: relative;
}
.landscape-pause::before {
  content: "";
  height: 14px;
  width: 1px;
  position: absolute;
  left: 0;
  background: #ffffff40;
}
.landscape-controls button:hover {
  background: #ffffff17;
}
@media (max-width: 580px) {
  .landscape-controls {
    top: 11px;
    right: 12px;
  }
}
@media (prefers-reduced-motion: reduce) {
  .landscape-dot > span {
    transition: none;
  }
}
</style>
