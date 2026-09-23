// build.js 以 esbuild define 注入 package.json 的 version
declare const __CLI_VERSION__: string;

export const VERSION = __CLI_VERSION__;
