// DAG 图对象 DagGraph
/**
 * @typedef {Object} DagGraph
 * @property {Node[]} nodes
 */ 

// 节点对象 Node
/**
 * @typedef {Object} Node
 * @property {string} id
 * @property {string} label
 * @property {string[]} inputFieldsIds
 * @property {string[]} outputFieldsIds
 * @property {string[]} preNodeIds
 * @property {string[]} nextNodeIds
 */

// 字段对象 Field
/**
 * @typedef {Object} Field
 * @property {string} id - 字段唯一标识
 * @property {string} name - 字段名
 * @property {string[]} dependendFieldIds - 依赖的输入字段id
 * @property {string} logic - 字段的产出逻辑
 */

// 逻辑对象 Logic
/**
 * @typedef {Object} Logic
 * @property {string} outputFieldId
 * @property {string[]} inputFieldIds
 * @property {string} description
 */