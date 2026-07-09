import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';

const publicDir = resolve(process.cwd(), 'public');
const siteUrl = (process.env.VITE_SITE_URL || 'https://meercat-b.vercel.app').replace(/\/+$/, '');

const routes = ['/', '/about', '/privacy', '/terms', '/disclaimer', '/contact'];

const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${routes
  .map((route) => `  <url>\n    <loc>${siteUrl}${route === '/' ? '/' : route}</loc>\n  </url>`)
  .join('\n')}
</urlset>
`;

const robots = `User-agent: *
Allow: /

Sitemap: ${siteUrl}/sitemap.xml
`;

await mkdir(publicDir, { recursive: true });
await writeFile(resolve(publicDir, 'sitemap.xml'), sitemap, 'utf8');
await writeFile(resolve(publicDir, 'robots.txt'), robots, 'utf8');
