import{C as e,R as t,S as n,mn as r,or as i,v as a,vn as o}from"./tokenStorage-Xv0D5hln.js";var s={prefix:Math.floor(Math.random()*1e4),current:0},c=Symbol(`elIdInjection`),l=()=>r()?o(c,s):s,u=r=>{let o=l();!e&&o===s&&t(`IdInjection`,`Looks like you are using server rendering, you must provide a id provider to ensure the hydration process to be succeed
usage: app.provide(ID_INJECTION_KEY, {
  prefix: number,
  current: number,
})`);let c=a();return n(()=>i(r)||`${c.value}-id-${o.prefix}-${o.current++}`)};export{l as n,u as t};