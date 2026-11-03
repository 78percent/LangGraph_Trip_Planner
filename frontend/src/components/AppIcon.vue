<script setup lang="ts">
withDefaults(defineProps<{ name: string; size?: number }>(), { size: 20 });
const paths: Record<string, string> = {
  compass:
    "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Zm4 5-2.5 5.5L8 16l2.5-5.5L16 8Z",
  arrow: "M4 12h16m-6-6 6 6-6 6",
  pause: "M8 5v14M16 5v14",
  play: "m8 4 12 8-12 8V4Z",
  diagonal: "M6 18 18 6M6 6h12v12",
  pin: "M19 10c0 5-7 11-7 11S5 15 5 10a7 7 0 1 1 14 0Zm-5 0a2 2 0 1 0-4 0 2 2 0 0 0 4 0Z",
  calendar:
    "M5 5h14a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2ZM7 3v4m10-4v4M3 11h18",
  chat: "M21 11.5a8.5 8.5 0 0 1-8.5 8.5H4l-2 2V11.5a9.5 9.5 0 0 1 19 0ZM7 11h10m-10 4h6",
  plus: "M12 5v14M5 12h14",
  leaf: "M20 3c-9-1-16 4-15 11 1 5 7 7 11 3 3-3 4-8 4-14ZM4 21 15 10",
  mountain: "m2 20 7-14 5 9 3-5 5 10H2Zm4-8 3 2 3-2",
  book: "M12 5C8 2 4 3 2 4v15c4-2 7-1 10 1m0-15c4-3 8-2 10-1v15c-4-2-7-1-10 1V5Z",
  cup: "M4 8h12v8a4 4 0 0 1-4 4H8a4 4 0 0 1-4-4V8Zm12 0h2a3 3 0 0 1 0 6h-2M6 3v2m4-2v2m4-2v2",
  art: "M12 3a9 9 0 1 0 0 18h1a2 2 0 0 0 1-4 1.5 1.5 0 0 1 1-3h3a3 3 0 0 0 3-3 9 9 0 0 0-9-8ZM7 9h.01M10 6h.01M15 6h.01M18 9h.01",
  send: "m22 2-7 20-4-9-9-4L22 2ZM11 13 22 2",
  route: "M6 5h9a4 4 0 0 1 0 8H9a4 4 0 0 0 0 8h9M6 2v6M3 5h6m9 13 3 3-3 3",
};
</script>

<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.6"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    focusable="false"
    class="app-icon"
  >
    <path :d="paths[name] || paths.compass" />
  </svg>
</template>
