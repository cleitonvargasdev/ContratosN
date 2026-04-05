<template>
  <section class="dashboard-grid">
    <article class="panel feature-panel">
      <p class="eyebrow">Resumo</p>
      <h2 class="panel__title">Painel inicial pronto para expansao</h2>
      <p class="panel__subtitle">
        A estrutura segue um estilo administrativo, com menu lateral em acordeao e area central pensada para modulos futuros.
      </p>
    </article>

    <article class="panel metric-panel">
      <span>Função atual</span>
      <strong>{{ auth.state.currentUser?.funcao }}</strong>
    </article>

    <article class="panel metric-panel metric-panel--accent">
      <span>Usuario autenticado</span>
      <strong>{{ auth.state.currentUser?.login }}</strong>
    </article>
  </section>
</template>

<script setup lang="ts">
import { useAuthController } from '@/controllers/useAuthController'

const auth = useAuthController()
</script>
