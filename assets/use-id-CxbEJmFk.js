import{Gi as e,Ht as t,Qr as n,Sn as r,mn as i,ni as a,pn as o}from"./api-UJwwwF-9.js";var s={prefix:Math.floor(Math.random()*1e4),current:0},c=Symbol(`elIdInjection`),l=()=>n()?a(c,s):s,u=n=>{let a=l();!i&&a===s&&r(`IdInjection`,`Looks like you are using server rendering, you must provide a id provider to ensure the hydration process to be succeed
usage: app.provide(ID_INJECTION_KEY, {
  prefix: number,
  current: number,
})`);let c=t();return o(()=>e(n)||`${c.value}-id-${a.prefix}-${a.current++}`)};export{l as n,u as t};