// ARK - site.config.json tipleri (template/site.config.schema.json ile birebir eslesir)

export interface SiteConfig {
  site_id: string;
  tier: "3D" | "7D";
  business: {
    name: string;
    sector_code: string;
    sector_name: string;
    city: string;
    address?: string;
    phone: string;
    whatsapp?: string;
    instagram?: string;
    email?: string;
  };
  design?: {
    primary_color?: string;
    secondary_color?: string;
    font_heading?: string;
    font_body?: string;
  };
  sections: {
    hero: { headline: string; subheadline?: string; video_asset: string; frame_count: number };
    services_grid: { items: { title: string; description?: string; icon?: string }[] };
    animation_2: { video_asset: string; frame_count: number };
    social_proof: {
      testimonials?: { author?: string; text?: string; rating?: number }[];
      photos?: string[];
    };
    contact: { map_embed?: string; hours?: string; cta_text: string };
  };
  media?: { customer_photos?: string[]; product_photos?: string[] };
  seo: {
    meta_title: string;
    meta_description: string;
    target_keywords: string[];
    og_image?: string;
  };
  deploy: { subdomain: string; status: "draft" | "review" | "live" };
}

export async function loadSiteConfig(url = "/site.config.json"): Promise<SiteConfig> {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`site.config.json yuklenemedi: ${res.status}`);
  }
  return res.json();
}
