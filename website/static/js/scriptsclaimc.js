document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('product-container');
    const productList = document.getElementById('product-listc');
    const editContainer = document.getElementById('edit-container');
    const editInput = document.getElementById('edit-input');
    const saveButton = document.getElementById('save-button');
    const cancelButton = document.getElementById('cancel-button');
    const addProductButton = document.getElementById('add-product-button');
    const removeProductButton = document.getElementById('remove-product-button');
    let currentProduct = null;

    let productsData = [];

    // Fetch products from the /products endpoint
    function fetchProducts() {
        fetch('/productsclaim')
            .then(response => response.json())
            .then(data => {
                productsData = data.products;
                renderProducts();
            })
            .catch(error => console.error('Error fetching products:', error));
    }

    function renderProducts() {
        container.innerHTML = '';
        productList.innerHTML = '';

        productsData.forEach((data, index) => {
            const product = document.createElement('div');
            product.className = 'product';
            product.textContent = data.name;
            container.appendChild(product);

            const listItem = document.createElement('li');
            listItem.textContent = data.name;
            listItem.dataset.index = index;
            productList.appendChild(listItem);

            listItem.addEventListener('click', () => {
                currentProduct = index;
                editInput.value = productsData[index].name;
                editContainer.classList.remove('hidden');
            });
        });
    }

    function addProduct(name) {
        productsData.push({ name, interval: 1000 });
        renderProducts();
    }

    function removeProduct(index) {
        if (index >= 0 && index < productsData.length) {
            productsData.splice(index, 1);
            renderProducts();
        }
    }

    saveButton.addEventListener('click', () => {
        if (currentProduct !== null) {
            productsData[currentProduct].name = editInput.value;
            renderProducts();
            editContainer.classList.add('hidden');
            currentProduct = null;
        }
    });

    cancelButton.addEventListener('click', () => {
        editContainer.classList.add('hidden');
        currentProduct = null;
    });

    addProductButton.addEventListener('click', () => {
        const newName = prompt('Enter new product name:');
        if (newName) {
            addProduct(newName);
        }
    });

    removeProductButton.addEventListener('click', () => {
        const index = parseInt(prompt('Enter index of product to remove (0-based):'), 10);
        if (!isNaN(index)) {
            removeProduct(index);
        }
    });

    // Fetch products and render them on page load
    fetchProducts();
});
