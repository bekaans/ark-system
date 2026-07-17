import "./style.css";
import { loadSiteConfig } from "./config";
import { renderSite } from "./sections";

const root = document.querySelector<HTMLDivElement>("#app")!;

loadSiteConfig()
  .then((config) => renderSite(root, config))
  .catch((err) => {
    root.innerHTML = `<div class="ark-error">site.config.json yuklenemedi: ${err.message}</div>`;
  });
