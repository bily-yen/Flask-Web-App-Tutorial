let cart = [];
let products = [];  // Global products array
let additionalProducts = [];  // Store additional products
let phones = [];    // Phones products
let furniture = []; // Furniture products
let clothing = [];  // Clothing products
let accessories = []; // Accessories products

async function fetchProducts() {
    try {
        const response = await fetch('/api/products');
        products = await response.json();  // General products
        displayProducts(products);  // Display general products
    } catch (error) {
        console.error('Error fetching products:', error);
    }
}

async function fetchAdditionalProducts() {
    try {
        const response = await fetch('/api/additional');
        const additionalProducts = await response.json();
        displayAdditionalProducts(additionalProducts);
    } catch (error) {
        console.error('Error fetching additional products:', error);
    }
}


async function fetchPhones() {
    try {
        const response = await fetch('/api/phones');
        phones = await response.json();  // Store phones products
        console.log("Phones fetched:", phones);
        displayPhones(phones);
    } catch (error) {
        console.error('Error fetching phones:', error);
    }
}

async function fetchFurniture() {
    try {
        const response = await fetch('/api/furniture');
        furniture = await response.json();  // Store furniture products
        console.log("Furniture fetched:", furniture);
        displayFurniture(furniture);
    } catch (error) {
        console.error('Error fetching furniture:', error);
    }
}

async function fetchClothing() {
    try {
        const response = await fetch('/api/clothing');
        clothing = await response.json();  // Store clothing products
        console.log("Clothing fetched:", clothing);
        displayClothing(clothing);
    } catch (error) {
        console.error('Error fetching clothing:', error);
    }
}

async function fetchAccessories() {
    try {
        const response = await fetch('/api/accessories');
        accessories = await response.json();  // Store accessories products
        console.log("Accessories fetched:", accessories);
        displayAccessories(accessories);
    } catch (error) {
        console.error('Error fetching accessories:', error);
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
function displayPhones(products) {
    const productContainer = document.getElementById('phones-product-section');
    productContainer.innerHTML = products.map((item, index) => createProductHTML(item, index)).join('');
}

function displayFurniture(products) {
    const productContainer = document.getElementById('furniture-product-section');
    productContainer.innerHTML = products.map((item, index) => createProductHTML(item, index)).join('');
}

function displayClothing(products) {
    const productContainer = document.getElementById('clothing-product-section');
    productContainer.innerHTML = products.map((item, index) => createProductHTML(item, index)).join('');
}

function displayAccessories(products) {
    const productContainer = document.getElementById('accessories-product-section');
    productContainer.innerHTML = products.map((item, index) => createProductHTML(item, index)).join('');
}

function createProductHTML(item) {
    const { id, image, name, price } = item;
    const imgSrc = image ? `/static/${image}` : '/static/SPAPHOTOS/placeholder-image.png';
    
    // Create a URL for the product details page dynamically using the product ID
    const productDetailUrl = `/product/${id}`;
    
    // Set the initial quantity value (always starts with 1 but can be modified)
    const initialQuantity = 1;  // Or get from the cart if needed

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
                        <label for="quantity-${id}" style="font-weight: bold;font-size:16px; margin-right: 5px;">Quantity:</label>
                        <input 
                            type="number" 
                            id="quantity-${id}" 
                            min="1" 
                            value="${initialQuantity}" 
                            placeholder="1" 
                            style="width: 50px; border: 2px solid #ccc; padding: 5px; border-radius: 5px;" 
                            title="Select the quantity you want to order"
                            onchange="updateQuantity(${id}, this.value)"  <!-- Bind the onchange event -->
                      
                    </div>
                </div>
                <button onclick='addToCart(${JSON.stringify(item)})'>Add to cart</button>
                <a href="${productDetailUrl}" class="prdetails-link">Details</a>
            </div>
        </div>
    `;
}

function updateQuantity(productId, newQuantity) {
    // Ensure the quantity is a valid number and at least 1
    newQuantity = parseInt(newQuantity, 10) || 1;  // Default to 1 if the input is invalid
    newQuantity = newQuantity < 1 ? 1 : newQuantity;  // Ensure minimum quantity is 1

    // Find the product in the cart (if it exists)
    const cartProduct = cart.find(item => item.id === productId);
    if (cartProduct) {
        // Update the product quantity in the cart
        cartProduct.quantity = newQuantity;
    } else {
        // If the product is not in the cart, add it with the new quantity
        const product = [...products, ...additionalProducts, ...phones, ...furniture, ...clothing, ...accessories]
            .find(item => item.id === productId);
        if (product) {
            cart.push({ ...product, quantity: newQuantity });
        }
    }

    // Update the displayed total price for the product
    const product = [...products, ...additionalProducts, ...phones, ...furniture, ...clothing, ...accessories]
        .find(item => item.id === productId);
    if (product) {
        // Update the displayed total price for the product based on the new quantity
        const totalPriceElement = document.getElementById(`product-total-${productId}`);
        if (totalPriceElement) {
            totalPriceElement.innerText = (product.price * newQuantity).toFixed(2);  // Update total price
        }
    }

    // Optionally, update cart total or cart UI as needed
    updateCartUI();
}
function addToCart(item) {
    const quantityInput = document.getElementById(`quantity-${item.id}`);
    
    // Log to check the input field and quantity value
    console.log('Adding to cart:', item.name);
    console.log('Quantity input:', quantityInput);

    if (!quantityInput) {
        console.error('Quantity input field not found for product:', item.name);
        return;  // Exit early if the input field is not found
    }



    const quantity = parseInt(quantityInput.value, 10) || 1;  // Default to 1 if input is invalid
    console.log('Quantity:', quantity);

    // Check if the product already exists in the cart
    const existingProductIndex = cart.findIndex(cartItem => cartItem.id === item.id);
    
    if (existingProductIndex > -1) {
        // Update the quantity if the product already exists in the cart
        console.log('Updating existing product in cart');
        cart[existingProductIndex].quantity;
    } else {
        // Add the product to the cart if it's not already there
        console.log('Adding new product to cart');
        cart.push({ ...item, quantity });
    }

    // Display updated cart
    displayCart();

    // Display a brief confirmation that the product was added to the cart
    showCartConfirmation(`${item.name} added to cart!`);

    // Move the cart icon slightly
    moveCartIcon();
}


function removeFromCart(index) {
    // Remove the item from the cart
    cart.splice(index, 1);

    // Display updated cart
    displayCart();
}

function showCartConfirmation(message) {
    // Create a small popup notification near the cart icon
    const notification = document.createElement('div');
    notification.classList.add('cart-notification');
    notification.innerHTML = message;
    
    // Append the notification to the body
    document.body.appendChild(notification);
    
    // Set a timeout to remove the notification after 2 seconds
    setTimeout(() => {
        notification.remove();
    }, 2000); // Remove the notification after 2 seconds
}

function moveCartIcon() {
    const cartIcon = document.querySelector('.cart');
    cartIcon.classList.add('moved'); // Add the 'moved' class to animate the cart icon
    
    // Reset the cart icon position after 2 seconds
    setTimeout(() => {
        cartIcon.classList.remove('moved');
    }, 2000);
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

// Function to show the notification in the center of the modal
function showNotification(message, loading = false) {
    const notification = document.getElementById('notification');
    const overlay = document.getElementById('overlay');
    const cartItem = document.getElementById('cartItem'); // Assuming the cart items container has an id 'cartItem'
    
    // Show loading spinner if needed
    const loadingSpinner = loading ? `<div class="spinner"></div>` : ''; 
    notification.innerHTML = `${loadingSpinner} ${message}`; // Set message and spinner
    notification.classList.add('show'); // Show notification
    
    // Show overlay and make background static
    overlay.classList.add('show');
    
    // Fade the cart content to show it's inactive
    cartItem.classList.add('faded');
    
    // Set timeout to hide notification and restore cart after 20 seconds
    setTimeout(() => {
        notification.classList.remove('show'); // Hide notification
        overlay.classList.remove('show'); // Hide overlay
        cartItem.classList.remove('faded'); // Restore cart
    }, 20000); // Show notification for 20 seconds
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

// Call the fetch functions for each category
fetchProducts();           // Fetch general products
fetchAdditionalProducts(); // Fetch additional products
fetchFurniture();          // Corrected function name
fetchClothing();           // Corrected function name
fetchPhones();             // Corrected function name
fetchAccessories(); 