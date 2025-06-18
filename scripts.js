function getClassName() {
  const params = new URLSearchParams(window.location.search);
  return params.get('name');
}

async function loadGraphs() {
  const className = getClassName();
  document.getElementById('class-title').textContent = `Graphs in ${className}`;

  try {
    const response = await fetch(`data/${className}.json`);
    const data = await response.json();

    const container = document.getElementById('graph-container');

    data.graphs.forEach((filename) => {
      const img = document.createElement('img');
      img.src = `data/${className}/${filename}`;
      img.classList.add('graph-image');

      // Add error logging if image fails to load
      img.onerror = () => console.error("❌ Failed to load image:", img.src);

      container.appendChild(img);
    });

  } catch (err) {
    console.error("❌ Failed to load JSON or render images:", err);
  }
}

// Load only if we're on the class page
if (window.location.pathname.endsWith('class.html')) {
  loadGraphs();
}
