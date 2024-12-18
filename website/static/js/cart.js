let cart = [];
let products = [];  // Global products array

// Fetch products from the API
async function fetchProducts() {
    try {
        const response = await fetch('/api/products');
        products = await response.json();  // Store products globally
        displayProducts(products);
    } catch (error) {
        console.error('Error fetching products:', error);
    }
}

// Fetch additional products from the API
async function fetchAdditionalProducts() {
    try {
        const response = await fetch('/api/additional');
        const additionalProducts = await response.json();
        displayAdditionalProducts(additionalProducts);
    } catch (error) {
        console.error('Error fetching additional products:', error);
    }
}

// Display products on the page
function displayProducts(products) {
    const productContainer = document.getElementById('productCatalog');
    productContainer.innerHTML = products.map((item, index) => createProductHTML(item, index)).join('');
}

// Display additional products on the page
function displayAdditionalProducts(products) {
    const additionalProductContainer = document.getElementById('additionalProductSection');
    additionalProductContainer.innerHTML = products.map((item, index) => createProductHTML(item, index)).join('');
}

// Create HTML for a product
function createProductHTML(item, index) {
    const { id, image, name, price } = item;
    const imgSrc = image ? `/static/${image}` : '/static/SPAPHOTOS/placeholder-image.png';
    
    // Create a URL for the product details page dynamically using the product ID
    const productDetailUrl = `/product/${id}`;

    return `
        <div class='box'>
            <div class='img-box'>
                <img class='images' src='${imgSrc}' alt='${name}' />
            </div>
            <div class='bottom'>
                <p>${name}</p>
                <h2>Ksh ${price}.00</h2>
                <div class='inputs'>
                    <div class='inputbox'>
                        <label for="quantity-${index}" style="font-weight: bold;font-size:16px; margin-right: 5px;">Quantity:</label>
                        <input 
                            type="number" 
                            id="quantity-${index}" 
                            min="1" 
                            value="1" 
                            placeholder="1" 
                            style="width: 50px; border: 2px solid #ccc; padding: 5px; border-radius: 5px;" 
                            title="Select the quantity you want to order"
                        />
                    </div>
                </div>
                <button onclick='addToCart(${index})'>Add to cart</button>
                <!-- Link to the product details page -->
                <a href="${productDetailUrl}" class="prdetails-link">View Details</a>
            </div>
        </div>
    `;
}

// Add product to the cart
function addToCart(index) {
    const quantityInput = document.getElementById(`quantity-${index}`);
    const quantity = parseInt(quantityInput.value, 10) || 1;

    const existingProductIndex = cart.findIndex(item => item.id === products[index].id);
    if (existingProductIndex > -1) {
        cart[existingProductIndex].quantity += quantity;
    } else {
        cart.push({ ...products[index], quantity });
    }

    displayCart();
}

// Remove product from the cart
function removeFromCart(index) {
    cart.splice(index, 1);
    displayCart();
}

// Display cart items
function displayCart() {
    const cartItemContainer = document.getElementById('cartItem');
    const countElement = document.getElementById('count');
    const totalElement = document.getElementById('total');

    if (cart.length === 0) {
        cartItemContainer.innerHTML = 'Your cart is empty';
        countElement.textContent = '0';
        totalElement.textContent = 'Ksh 0.00';
        return;
    }

    cartItemContainer.innerHTML = cart.map((item, index) => createCartItemHTML(item, index)).join('');
    countElement.textContent = cart.length;
    totalElement.textContent = `Ksh ${calculateTotal().toFixed(2)}`;
}

// Create HTML for each cart item
function createCartItemHTML(item, index) {
    return `
        <div class="cart-item">
            <p>${item.name} (Quantity: ${item.quantity})</p>
            <p>Ksh ${item.price}.00</p>
            <p>Total: Ksh ${(item.price * item.quantity).toFixed(2)}</p>
            <button class="remove-button" onclick="removeFromCart(${index})">✖</button>
        </div>
    `;
}

// Calculate the total price of the cart
function calculateTotal() {
    return cart.reduce((acc, item) => acc + item.price * item.quantity, 0);
}

// Validate phone number format (Kenya - starting with 254)
function validatePhoneNumber(phone) {
    return phone.startsWith('254') && phone.length === 12;
}

// Format the phone number input for Kenyan format
function formatPhoneNumber(event) {
    const input = event.target;
    let phoneNumber = input.value.replace(/\D/g, '');

    if (phoneNumber.length === 10 && phoneNumber.startsWith('0')) {
        phoneNumber = '254' + phoneNumber.substring(1);
    } else if (phoneNumber.length === 9 && phoneNumber.startsWith('7')) {
        phoneNumber = '254' + phoneNumber;
    }

    input.value = phoneNumber;
}

// Show notification (success/error messages)
function showNotification(message, loading = false) {
    const notification = document.getElementById('notification');
    const loadingSpinner = loading ? `<div class="spinner"></div>` : '';
    notification.innerHTML = `${loadingSpinner} ${message}`;
    notification.classList.add('show');

    setTimeout(() => {
        notification.classList.remove('show');
    }, 20000);  // Notification timeout of 20 seconds
}

// Process payment
async function processPayment() {
    const phoneInput = document.getElementById('phone').value;
    const formattedPhone = phoneInput.replace(/\D/g, '');

    if (!validatePhoneNumber(formattedPhone)) {
        showNotification('Please enter a valid 12-digit phone number starting with 254.');
        return;
    }

    const totalAmount = calculateTotal();

    if (totalAmount <= 0) {
        showNotification('Your cart is empty. Please add items before proceeding to payment.');
        return;
    }

    const productIds = cart.map(item => `${item.id}:${item.quantity}`).join(',');
    const paymentData = { amount: totalAmount, phone: formattedPhone, product_ids: productIds };

    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

    showNotification('Payment initiated, please wait...', true);

    try {
        const response = await fetch('/pay', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(paymentData)
        });

        const result = await response.json();

        if (response.ok) {
            showNotification('Payment initiated successfully. Please check your phone for confirmation.', true);
        } else {
            showNotification('Payment initiation failed. Please try again later.');
        }
    } catch (error) {
        showNotification('An error occurred. Please try again later.');
        console.error('Payment error:', error);
    }
}

// Call fetch functions on page load
fetchProducts();
fetchAdditionalProducts();