<template>
  <div class="dag-editor-full">
    <div class="dag-mode-switch">
      <el-switch
        v-model="isEditMode"
        active-text="编辑模式"
        inactive-text="查看模式"
        inline-prompt
        style="margin-right: 24px;"
      />
    </div>
    <div ref="container" class="dag-graph-container"></div>
    <div v-if="editingNodeId && isEditMode" class="node-edit-bar">
      <input
        ref="editInputRef"
        v-model="editInputValue"
        class="node-edit-input"
        @keydown.enter="saveEdit"
        @keydown.esc="cancelEdit"
        @blur="saveEdit"
        maxlength="20"
        autofocus
      />
    </div>
    <div class="dag-toolbar">
      <el-button @click="addNode" v-if="isEditMode">添加节点</el-button>
      <el-button v-if="selectedNodeId && isEditMode" type="danger" @click="deleteNode">删除节点</el-button>
    </div>
    <div v-if="selectedNodeId" class="logic-btn-bar">
      <el-button type="primary" @click="showLogicEditor = true">查看逻辑</el-button>
    </div>
    <el-dialog v-model="showLogicEditor" title="节点逻辑查看/编辑" width="900px" :close-on-click-modal="false">
      <NodeLogicEditor
        v-if="currentNodeForLogic"
        :node="currentNodeForLogic"
        :isEditMode="isEditMode"
      />
      <template #footer>
        <el-button @click="showLogicEditor = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick, watch, computed } from 'vue'
import { Graph } from '@antv/x6'
import NodeLogicEditor from '@/pages/NodeLogicEditor.vue'

const container = ref(null)
let graph = null
const selectedNodeId = ref(null)
const editingNodeId = ref(null)
const nodeLabels = ref({}) // { [id]: label }
const editInputValue = ref('')
const editInputRef = ref(null)
const isEditMode = ref(true)
const showLogicEditor = ref(false)

const currentNodeForLogic = computed(() => {
  if (!selectedNodeId.value) return null
  // 构造当前节点对象，包含 inputFields/outputFields/logic
  // 这里只做演示，实际应从你的节点数据结构中获取
  return {
    id: selectedNodeId.value,
    label: nodeLabels.value[selectedNodeId.value] || '',
    inputFields: [], // TODO: 从你的全局数据获取
    outputFields: [], // TODO: 从你的全局数据获取
    logic: [] // TODO: 从你的全局数据获取
  }
})

watch(editInputValue, (val) => {
  if (editingNodeId.value) {
    const node = graph.getCellById(editingNodeId.value)
    if (node) {
      node.setLabel(val)
    }
  }
})

watch(isEditMode, async (val) => {
  if (graph) {
    await nextTick()
    try {
      // 更新连线配置
      graph.options.connecting = {
        ...graph.options.connecting,
        allowEdge: false,
        allowNode: val,
        allowBlank: false,
        allowLoop: false,
        highlight: true,
        snap: true,
        validateConnection({ sourceCell, targetCell }) {
          return sourceCell.id !== targetCell.id && val
        },
        createEdge() {
          return graph.createEdge({
            attrs: {
              line: {
                stroke: '#A2B1C3',
                strokeWidth: 2,
                targetMarker: {
                  name: 'block',
                  width: 12,
                  height: 8,
                },
              },
            },
          })
        },
      }

      // 更新节点和连线的交互状态
      const nodes = graph.getNodes()
      if (nodes && nodes.length) {
        nodes.forEach(node => {
          if (node && node.setData) {
            node.setData({ draggable: true })
            node.attr('body/cursor', 'move')
            // 编辑模式下显示锚点，查看模式下隐藏锚点
            node.getPorts().forEach(port => {
              node.setPortProp(port.id, 'attrs/circle/style/display', val ? '' : 'none')
            })
          }
        })
      }

      const edges = graph.getEdges()
      if (edges && edges.length) {
        edges.forEach(edge => {
          if (edge && edge.attr) {
            edge.attr('line/cursor', 'pointer')
          }
        })
      }
    } catch (error) {
      console.warn('更新图形属性失败:', error)
    }
  }
})

function resizeGraph() {
  if (graph && container.value) {
    graph.resize(container.value.clientWidth, container.value.clientHeight)
  }
}

function clearNodeHighlight() {
  if (selectedNodeId.value) {
    const node = graph.getCellById(selectedNodeId.value)
    if (node) {
      node.setAttrs({ body: { stroke: '#5F95FF', strokeWidth: 1 } })
    }
    selectedNodeId.value = null
  }
}

function highlightNode(id) {
  const node = graph.getCellById(id)
  if (node) {
    node.setAttrs({ body: { stroke: '#f56c6c', strokeWidth: 3 } })
  }
}

function startEditNode(id) {
  if (!isEditMode.value) return
  editingNodeId.value = id
  editInputValue.value = nodeLabels.value[id] || '新节点'
  nextTick(() => {
    if (editInputRef.value) {
      editInputRef.value.focus()
      editInputRef.value.select()
    }
  })
}

function saveEdit() {
  if (editingNodeId.value && editInputValue.value.trim()) {
    nodeLabels.value[editingNodeId.value] = editInputValue.value.trim()
    const node = graph.getCellById(editingNodeId.value)
    if (node) node.setLabel(editInputValue.value.trim())
  }
  editingNodeId.value = null
}

function cancelEdit() {
  editingNodeId.value = null
}

onMounted(async () => {
  await nextTick()
  try {
    graph = new Graph({
      container: container.value,
      width: container.value.clientWidth,
      height: container.value.clientHeight,
      grid: true,
      connecting: {
        connector: 'smooth',
        anchor: 'center',
        connectionPoint: 'anchor',
        allowBlank: false,
        highlight: true,
        snap: true,
        allowLoop: false,
        allowNode: isEditMode.value,
        allowEdge: false,
        validateConnection({ sourceCell, targetCell }) {
          return sourceCell.id !== targetCell.id && isEditMode.value
        },
        createEdge() {
          return graph.createEdge({
            attrs: {
              line: {
                stroke: '#A2B1C3',
                strokeWidth: 2,
                targetMarker: {
                  name: 'block',
                  width: 12,
                  height: 8,
                },
              },
            },
          })
        },
      },
      selecting: {
        enabled: true,
        multiple: false,
        rubberband: true,
        showNodeSelectionBox: true,
        showEdgeSelectionBox: true,
      },
      keyboard: {
        enabled: true,
      },
      clipboard: {
        enabled: true,
      },
    })

    window.addEventListener('resize', resizeGraph)

    // 选中节点高亮
    graph.on('node:click', ({ node }) => {
      if (selectedNodeId.value && selectedNodeId.value !== node.id) {
        clearNodeHighlight()
      }
      selectedNodeId.value = node.id
      highlightNode(node.id)
    })

    // 选中连线高亮
    graph.on('edge:click', ({ edge }) => {
      graph.getEdges().forEach(e => e.setAttrs({ line: { stroke: '#A2B1C3', strokeWidth: 2 } }))
      edge.setAttrs({ line: { stroke: '#f56c6c', strokeWidth: 3 } })
    })

    // 点击空白处取消选中
    graph.on('blank:click', () => {
      clearNodeHighlight()
      graph.getEdges().forEach(e => e.setAttrs({ line: { stroke: '#A2B1C3', strokeWidth: 2 } }))
    })

    // 右键删除节点
    graph.on('node:contextmenu', ({ node, e }) => {
      if (!isEditMode.value) return
      e.preventDefault()
      if (window.confirm('删除该节点？')) {
        if (selectedNodeId.value && selectedNodeId.value === node.id) {
          selectedNodeId.value = null
        }
        node.remove()
        delete nodeLabels.value[node.id]
      }
    })

    // 右键删除连线
    graph.on('edge:contextmenu', ({ edge, e }) => {
      if (!isEditMode.value) return
      e.preventDefault()
      if (window.confirm('删除该连线？')) {
        edge.remove()
      }
    })

    // 双击节点，显示下方编辑栏
    graph.on('node:dblclick', ({ node }) => {
      startEditNode(node.id)
    })
  } catch (error) {
    console.error('初始化图形失败:', error)
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeGraph)
  if (graph) {
    try {
      graph.dispose()
    } catch (error) {
      console.warn('清理图形实例失败:', error)
    }
  }
})

function addNode() {
  if (!isEditMode.value) return
  const id = `${Date.now()}_${Math.floor(Math.random()*10000)}`
  nodeLabels.value[id] = '新节点'
  graph.addNode({
    id,
    x: Math.random() * 600,
    y: Math.random() * 400,
    width: 100,
    height: 40,
    label: '新节点',
    attrs: {
      body: {
        stroke: '#5F95FF',
        strokeWidth: 1,
        fill: '#fff',
      },
      label: {
        fontSize: 14,
        fill: '#333',
      }
    },
    data: {
      label: '新节点',
    },
    ports: {
      groups: {
        // 四周锚点
        top: {
          position: 'top',
          attrs: { circle: { r: 4, magnet: true, stroke: '#5F95FF', strokeWidth: 1, fill: '#fff' } }
        },
        right: {
          position: 'right',
          attrs: { circle: { r: 4, magnet: true, stroke: '#5F95FF', strokeWidth: 1, fill: '#fff' } }
        },
        bottom: {
          position: 'bottom',
          attrs: { circle: { r: 4, magnet: true, stroke: '#5F95FF', strokeWidth: 1, fill: '#fff' } }
        },
        left: {
          position: 'left',
          attrs: { circle: { r: 4, magnet: true, stroke: '#5F95FF', strokeWidth: 1, fill: '#fff' } }
        }
      },
      items: [
        { id: 'port_top', group: 'top' },
        { id: 'port_right', group: 'right' },
        { id: 'port_bottom', group: 'bottom' },
        { id: 'port_left', group: 'left' }
      ]
    }
  })
}

function deleteNode() {
  if (!isEditMode.value) return
  if (selectedNodeId.value) {
    const node = graph.getCellById(selectedNodeId.value)
    if (node) node.remove()
    delete nodeLabels.value[selectedNodeId.value]
    selectedNodeId.value = null
  }
}
</script>

<style scoped>
.dag-editor-full {
  position: fixed;
  inset: 0;
  display: flex;
  flex-direction: column;
}
.dag-mode-switch {
  position: absolute;
  top: 16px;
  right: 32px;
  z-index: 10;
}
.dag-graph-container {
  flex: 1 1 0;
  min-height: 0;
  min-width: 0;
  border: 1px solid #eee;
}
.dag-toolbar {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 16px 0;
  background: #fff;
  border-top: 1px solid #eee;
  box-shadow: 0 -2px 8px #f5f5f5;
  gap: 16px;
}
.node-edit-bar {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #f8f8f8;
  border-top: 1px solid #eee;
  padding: 18px 0 8px 0;
}
.node-edit-input {
  font-size: 16px;
  padding: 6px 16px;
  border: 1px solid #5F95FF;
  border-radius: 4px;
  outline: none;
  min-width: 120px;
  max-width: 240px;
  background: #fff;
}
.logic-btn-bar {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 8px 0 0 0;
  background: none;
}
</style> 