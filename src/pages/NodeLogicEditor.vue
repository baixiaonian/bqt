<template>
  <div class="node-logic-editor">
    <!-- 左侧输入字段 -->
    <div class="field-list input-list">
      <h3>输入字段</h3>
      <ul>
        <li v-for="field in inputFields" :key="field.id">
          {{ field.name }}
        </li>
      </ul>
      <el-button v-if="isEditMode" @click="addInputField">添加输入字段</el-button>
    </div>
    <!-- 中间逻辑区 -->
    <div class="logic-center">
      <div v-if="selectedOutputField">
        <h3>逻辑说明</h3>
        <el-input
          v-if="isEditMode"
          type="textarea"
          v-model="currentLogic.description"
          :rows="6"
          placeholder="请输入逻辑说明（支持Markdown）"
        />
        <div v-else v-html="renderMarkdown(currentLogic.description)" class="md-preview"></div>
        <!-- 依赖关系可视化区域（后续实现） -->
      </div>
      <div v-else>
        <span>请选择一个输出字段查看逻辑</span>
      </div>
    </div>
    <!-- 右侧输出字段 -->
    <div class="field-list output-list">
      <h3>输出字段</h3>
      <ul>
        <li
          v-for="field in outputFields"
          :key="field.id"
          :class="{ selected: field.id === selectedOutputFieldId }"
          @click="selectOutputField(field.id)"
        >
          {{ field.name }}
          <el-button v-if="isEditMode" @click.stop="removeOutputField(field.id)" type="text" size="small">删除</el-button>
        </li>
      </ul>
      <el-button v-if="isEditMode" @click="addOutputField">添加输出字段</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { marked } from 'marked'
const props = defineProps({
  node: Object,
  isEditMode: Boolean
})

const inputFields = ref([...props.node.inputFields])
const outputFields = ref([...props.node.outputFields])
const logics = ref([...props.node.logic])

const selectedOutputFieldId = ref(outputFields.value[0]?.id || null)
const selectedOutputField = computed(() =>
  outputFields.value.find(f => f.id === selectedOutputFieldId.value)
)
const currentLogic = computed(() =>
  logics.value.find(l => l.outputFieldId === selectedOutputFieldId.value) || { description: '', inputFieldIds: [] }
)

function selectOutputField(id) {
  selectedOutputFieldId.value = id
}
function addInputField() {
  const id = 'input_' + Date.now()
  inputFields.value.push({
    id,
    name: '新输入字段',
    type: 'input',
    path: [props.node.id]
  })
}
function addOutputField() {
  const id = 'output_' + Date.now()
  outputFields.value.push({
    id,
    name: '新输出字段',
    type: 'output',
    path: [props.node.id]
  })
  logics.value.push({
    outputFieldId: id,
    inputFieldIds: [],
    description: ''
  })
}
function removeOutputField(id) {
  const idx = outputFields.value.findIndex(f => f.id === id)
  if (idx !== -1) outputFields.value.splice(idx, 1)
  const logicIdx = logics.value.findIndex(l => l.outputFieldId === id)
  if (logicIdx !== -1) logics.value.splice(logicIdx, 1)
  if (selectedOutputFieldId.value === id) selectedOutputFieldId.value = outputFields.value[0]?.id || null
}
function renderMarkdown(md) {
  return marked(md || '')
}
</script>

<style scoped>
.node-logic-editor {
  display: flex;
  flex-direction: row;
  width: 100%;
  height: 100%;
}
.field-list {
  width: 200px;
  padding: 16px;
  border-right: 1px solid #eee;
}
.input-list {
  border-right: 1px solid #eee;
}
.output-list {
  border-left: 1px solid #eee;
}
.logic-center {
  flex: 1;
  padding: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.selected {
  background: #e6f7ff;
}
.md-preview {
  background: #fafbfc;
  border: 1px solid #eee;
  padding: 12px;
  border-radius: 4px;
  min-height: 80px;
  width: 100%;
}
</style> 