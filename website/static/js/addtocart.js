let cart = [];
let products = [];  // Global products array

async function fetchProducts() {
    try {
        const response = await fetch('/api/products');
        products = await response.json();  // Store products globally
        displayProducts(products);
    } catch (error) {
        console.error('Error fetching products:', error);
    }
}

async function fetchAdditionalProducts() {
    try {
        const response = await fetch('/api/additional'); // Updated endpoint for additional products
        const additionalProducts = await response.json();
        displayAdditionalProducts(additionalProducts);
    } catch (error) {
        console.error('Error fetching additional products:', error);
    }
}

function displayProducts(products) {
    const productContainer = document.getElementById('root');
    productContainer.innerHTML = products.map((item, index) => createProductHTML(item, index)).join('');
}

function displayAdditionalProducts(products) {
    const additionalProductContainer = document.getElementById('another-product-section');
    additionalProductContainer.innerHTML = products.map((item, index) => createProductHTML(item, index)).join('');
}

function createProductHTML(item, index) {
    const { id, image, name, price } = item;
    const imgSrc = image ? `/static/${image}` : '/static/SPAPHOTOS/placeholder-image.png';
    
    // Create a URL for the product details page dynamically using the product ID
    const productDetailUrl = `/product/${id}`;  // This assumes your Flask route for product details is '/product/<int:product_id>'
    
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

function removeFromCart(index) {
    cart.splice(index, 1);
    displayCart();
}

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

function calculateTotal() {
    return cart.reduce((acc, item) => acc + item.price * item.quantity, 0);
}

function validatePhoneNumber(phone) {
    return phone.startsWith('254') && phone.length === 12;
}

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

function showNotification(message, loading = false) {
    const notification = document.getElementById('notification');
    const loadingSpinner = loading ? `<div class="spinner"></div>` : ''; // Spinner for loading state
    notification.innerHTML = `${loadingSpinner} ${message}`; // Set the message and spinner
    notification.classList.add('show'); // Display the notification

    setTimeout(() => {
        notification.classList.remove('show'); // Hide notification after 20 seconds
    }, 20000); // Changed from 10000ms (10 seconds) to 20000ms (20 seconds)
}


async function processPayment() {
    const phoneInput = document.getElementById('phone').value;
    const formattedPhone = phoneInput.replace(/\D/g, ''); // Remove non-digit characters

    if (!validatePhoneNumber(formattedPhone)) { // Check phone number validity
        showNotification('Please enter a valid 12-digit phone number starting with 254.');
        return;
    }

    const totalAmount = calculateTotal(); // Calculate the total amount in the cart
    
    if (totalAmount <= 0) { // Check if cart is empty
        showNotification('Your cart is empty. Please add items before proceeding to payment.');
        return;
    }

    // Collect product data
    const productIds = cart.map(item => `${item.id}:${item.quantity}`).join(',');
    const paymentData = {
        amount: totalAmount,
        phone: formattedPhone,
        product_ids: productIds
    };

    console.log('Payment data:', paymentData);

    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content'); // Get CSRF token for security

    // Show loading notification for payment processing
    showNotification('Payment initiated, please wait...', true);

    try {
        // Send payment data to the server
        const response = await fetch('/pay', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken // Include CSRF token for security
            },
            body: JSON.stringify(paymentData) // Send payment data
        });

        const result = await response.json();
        
        if (response.ok) {
            // Show success notification for payment initiation
            showNotification('Payment initiated successfully. Please check your phone for confirmation.', true);

            // After payment initiation, ask for the pin
            showNotification('Please enter the pin sent to your phone.', true);
        } else {
            // Show a message only if the response is not successful
            showNotification('Payment initiation failed. Please try again later.');
        }
    } catch (error){
        // Show error notification if there is a problem with the payment process
        showNotification('An error occurred. Please try again later.');
        console.error('Payment error:', error);
    }
}

function showNotification(message, loading = false) {
    const notification = document.getElementById('notification');
    const loadingSpinner = loading ? `<div class="spinner"></div>` : ''; // Spinner for loading state
    notification.innerHTML = `${loadingSpinner} ${message}`; // Set the message and spinner
    notification.classList.add('show'); // Display the notification

    setTimeout(() => {
        notification.classList.remove('show'); // Hide notification after 20 seconds
    }, 20000); // Timeout set to 20 seconds
}
// Call fetchProducts and fetchAdditionalProducts on page load
fetchProducts();
fetchAdditionalProducts();