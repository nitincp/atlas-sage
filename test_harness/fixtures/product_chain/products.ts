interface Product {
  id: number;
  name: string;
  price: number;
}

async function loadProducts(): Promise<void> {
  const list = document.getElementById('product-list')!;
  const template = document.getElementById('product-card-template') as HTMLTemplateElement;

  const response = await fetch('/api/products');
  const products: Product[] = await response.json();

  list.innerHTML = '';

  for (const product of products) {
    const card = template.content.cloneNode(true) as DocumentFragment;

    const el = card.querySelector('.product-card')!;
    el.classList.remove('product-card--loading');

    card.querySelector('.product-card__title')!.textContent = product.name;
    card.querySelector('.product-card__price')!.textContent = `$${product.price.toFixed(2)}`;

    list.appendChild(card);
  }
}

document.addEventListener('DOMContentLoaded', loadProducts);
