<template>
  <section class="panel feature-panel module-placeholder">
    <p class="eyebrow">{{ groupLabel }}</p>
    <h2 class="panel__title">{{ titleLabel }}</h2>
    <p class="panel__subtitle">
      Este módulo foi previsto no menu e está reservado para a próxima etapa de implementação.
    </p>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const titleLabel = computed(() => {
  const rawTitle = route.query.titulo
  return typeof rawTitle === 'string' && rawTitle.trim() ? rawTitle : 'Módulo em preparação'
})

const groupLabel = computed(() => {
  const rawGroup = route.query.grupo
  return typeof rawGroup === 'string' && rawGroup.trim() ? rawGroup : 'Módulo'
})
</script>