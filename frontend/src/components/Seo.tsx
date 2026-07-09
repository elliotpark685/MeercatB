import { useEffect } from 'react';

type SeoProps = {
  title: string;
  description: string;
  path?: string;
};

const SITE_URL = import.meta.env.VITE_SITE_URL ?? 'https://meercat-b.vercel.app';

function upsertMeta(name: string, content: string) {
  let tag = document.querySelector<HTMLMetaElement>(`meta[name="${name}"]`);
  if (!tag) {
    tag = document.createElement('meta');
    tag.setAttribute('name', name);
    document.head.appendChild(tag);
  }
  tag.setAttribute('content', content);
}

function upsertProperty(property: string, content: string) {
  let tag = document.querySelector<HTMLMetaElement>(`meta[property="${property}"]`);
  if (!tag) {
    tag = document.createElement('meta');
    tag.setAttribute('property', property);
    document.head.appendChild(tag);
  }
  tag.setAttribute('content', content);
}

function upsertCanonical(url: string) {
  let tag = document.querySelector<HTMLLinkElement>('link[rel="canonical"]');
  if (!tag) {
    tag = document.createElement('link');
    tag.setAttribute('rel', 'canonical');
    document.head.appendChild(tag);
  }
  tag.setAttribute('href', url);
}

export default function Seo({ title, description, path = '/' }: SeoProps) {
  useEffect(() => {
    document.title = title;
    upsertMeta('description', description);
    upsertMeta('robots', 'index,follow');
    upsertMeta('theme-color', '#121212');
    upsertProperty('og:title', title);
    upsertProperty('og:description', description);
    upsertProperty('og:type', 'website');
    upsertProperty('og:url', new URL(path, SITE_URL).toString());
    upsertMeta('twitter:card', 'summary_large_image');
    upsertMeta('twitter:title', title);
    upsertMeta('twitter:description', description);
    upsertCanonical(new URL(path, SITE_URL).toString());
  }, [title, description, path]);

  return null;
}
