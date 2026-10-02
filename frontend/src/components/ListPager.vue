<script setup lang="ts">
/**
 * @brief 全站统一的列表分页器
 *
 * 列表页的分页外观(居中容器 + 背景页码按钮 + 总数)集中在这里维护,
 * 页面只传页码/每页数量/总数, 不再各自写容器样式与 el-pagination 属性
 */
import { computed } from 'vue'

const props = defineProps<{
  /** 当前页码 */
  page: number
  /** 每页数量 */
  pageSize: number
  /** 记录总数 */
  total: number
}>()

const emit = defineEmits<{
  (e: 'update:page', page: number): void
}>()

/** 数据只有一页时不渲染: 没有可翻的页, 分页器只是噪音 */
const visible = computed(() => props.total > props.pageSize)
</script>

<template>
  <div v-if="visible" class="pager-row">
    <el-pagination
      :current-page="page"
      :page-size="pageSize"
      :total="total"
      layout="prev, pager, next, total"
      background
      @current-change="emit('update:page', $event)"
    />
  </div>
</template>

<style scoped>
.pager-row {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}
</style>
