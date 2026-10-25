(() => {
  const data = window.GALLERY_DATA || { pc: [], phone: [] };
  const grid = document.getElementById('gallery-grid');
  const empty = document.getElementById('empty-state');
  const resultCount = document.getElementById('result-count');
  const search = document.getElementById('search');
  const buttons = [...document.querySelectorAll('.filter-button')];
  const dialog = document.getElementById('preview-dialog');
  const previewImage = document.getElementById('preview-image');
  const previewTitle = document.getElementById('preview-title');
  const previewKind = document.getElementById('preview-kind');
  const previewResolution = document.getElementById('preview-resolution');
  const formatDownloads = document.getElementById('format-downloads');
  let activeType = 'pc';
  let activeItem = null;

  document.getElementById('pc-count').textContent = String(data.pc.length);
  document.getElementById('phone-count').textContent = String(data.phone.length);

  function matches(item, query) {
    if (!query) return true;
    return String(item.number).includes(query) || item.filename.toLowerCase().includes(query.toLowerCase());
  }

  function openPreview(item) {
    activeItem = item;
    const selectedVariant = activeType === 'pc' ? item.variants.pc : item.variants.mobile;
    previewImage.src = selectedVariant.src;
    previewImage.alt = `${item.title}, ${activeType === 'pc' ? 'PC' : 'mobile'} wallpaper`;
    previewTitle.textContent = item.title;
    previewKind.textContent = activeType === 'pc' ? 'PC WALLPAPER' : 'MOBILE WALLPAPER';
    const sourceSize = activeType === 'pc' ? item.sourcePc : item.sourceMobile;
    previewResolution.textContent = `UPSCALED FROM ${sourceSize[0]} × ${sourceSize[1]} PX`;
    formatDownloads.replaceChildren();
    for (const [key, label] of [['pc', 'PC'], ['tablet', 'TABLET'], ['mobile', 'MOBILE']]) {
      const variant = item.variants[key];
      const link = document.createElement('a');
      link.className = 'format-download';
      link.href = variant.src;
      link.download = `noctra-${item.filename}-${key}.webp`;
      const name = document.createElement('span');
      name.className = 'format-name';
      name.textContent = label;
      const size = document.createElement('span');
      size.className = 'format-size';
      size.textContent = `${variant.width} × ${variant.height}`;
      link.append(name, size);
      formatDownloads.append(link);
    }
    if (typeof dialog.showModal === 'function') dialog.showModal();
    else window.open(item.src, '_blank', 'noopener');
  }

  function render() {
    const items = data[activeType] || [];
    const query = search.value.trim();
    const visible = items.filter(item => matches(item, query));
    grid.replaceChildren();
    resultCount.textContent = `${visible.length} WALLPAPER${visible.length === 1 ? '' : 'S'} · ${activeType === 'pc' ? 'PC' : 'MOBILE'} ${query ? '· SEARCHED' : ''}`;
    empty.hidden = visible.length > 0;
    grid.hidden = visible.length === 0;

    const fragment = document.createDocumentFragment();
    for (const item of visible) {
      const card = document.createElement('article');
      card.className = 'wallpaper-card';
      card.dataset.kind = activeType;
      card.tabIndex = 0;
      card.setAttribute('role', 'button');
      card.setAttribute('aria-label', `Preview ${item.title}, ${item.width} by ${item.height} pixels`);

      const visual = document.createElement('div');
      visual.className = 'wallpaper-visual';
      const image = document.createElement('img');
      image.src = item.src;
      image.alt = '';
      image.loading = 'lazy';
      image.decoding = 'async';
      const shade = document.createElement('div');
      shade.className = 'card-shade';
      const number = document.createElement('span');
      number.className = 'card-number';
      number.textContent = String(item.number).padStart(3, '0');
      const dims = document.createElement('span');
      dims.className = 'card-dimensions';
      dims.textContent = `${item.width} × ${item.height}`;
      const open = document.createElement('span');
      open.className = 'card-open';
      open.setAttribute('aria-hidden', 'true');
      open.textContent = '↗';
      visual.append(image, shade, number, dims, open);

      const info = document.createElement('div');
      info.className = 'card-info';
      const title = document.createElement('span');
      title.className = 'card-title';
      title.textContent = item.title;
      const type = document.createElement('span');
      type.className = 'card-type';
      type.textContent = activeType === 'pc' ? 'DESKTOP' : 'PHONE';
      info.append(title, type);
      card.append(visual, info);
      card.addEventListener('click', () => openPreview(item));
      card.addEventListener('keydown', event => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          openPreview(item);
        }
      });
      fragment.append(card);
    }
    grid.append(fragment);
  }

  buttons.forEach(button => button.addEventListener('click', () => {
    activeType = button.dataset.type;
    buttons.forEach(candidate => {
      const active = candidate === button;
      candidate.classList.toggle('is-active', active);
      candidate.setAttribute('aria-pressed', String(active));
    });
    render();
  }));
  search.addEventListener('input', render);
  document.getElementById('dialog-close').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => { if (event.target === dialog) dialog.close(); });
  document.addEventListener('keydown', event => {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
      event.preventDefault();
      search.focus();
    }
    if (event.key === 'Escape' && dialog.open) dialog.close();
  });
  render();
})();
