let cart = [];
let hpPhotocopiers = [];
let epsonPhotocopiers = [];
let ricohPhotocopiers = [];
let canonPhotocopiers = [];

// Fetch HP photocopiers
async function fetchHPPhotocopiers() {
    try {
        const response = await fetch('/api/hp-photocopiers');
        hpPhotocopiers = await response.json();
        displayHPPhotocopiers(hpPhotocopiers);
    } catch (error) {
        console.error('Error fetching HP photocopiers:', error);
    }
}

// Fetch Epson photocopiers
async function fetchEpsonPhotocopiers() {
    try {
        const response = await fetch('/api/epson-photocopiers');
        epsonPhotocopiers = await response.json();
        displayEpsonPhotocopiers(epsonPhotocopiers);
    } catch (error) {
        console.error('Error fetching Epson photocopiers:', error);
    }
}

// Fetch Ricoh photocopiers
async function fetchRicohPhotocopiers() {
    try {
        const response = await fetch('/api/ricoh-photocopiers');
        ricohPhotocopiers = await response.json();
        displayRicohPhotocopiers(ricohPhotocopiers);
    } catch (error) {
        console.error('Error fetching Ricoh photocopiers:', error);
    }
}

// Fetch Canon photocopiers
async function fetchCanonPhotocopiers() {
    try {
        const response = await fetch('/api/canon-photocopiers');
        canonPhotocopiers = await response.json();
        displayCanonPhotocopiers(canonPhotocopiers);
    } catch (error) {
        console.error('Error fetching Canon photocopiers:', error);
    }
}

// Display HP photocopiers
function displayHPPhotocopiers(products) {
    const hpProductContainer = document.getElementById('hp-photocopier-section');
    hpProductContainer.innerHTML = products.map((item, index) => createProductHTML(item, index, 'hp')).join('');
}

// Display Epson photocopiers
function displayEpsonPhotocopiers(products) {
    const epsonProductContainer = document.getElementById('epson-photocopier-section');
    epsonProductContainer.innerHTML = products.map((item, index) => createProductHTML(item, index, 'epson')).join('');
}

// Display Ricoh photocopiers
function displayRicohPhotocopiers(products) {
    const ricohProductContainer = document.getElementById('ricoh-photocopier-section');
    ricohProductContainer.innerHTML = products.map((item, index) => createProductHTML(item, index, 'ricoh')).join('');
}

// Display Canon photocopiers
function displayCanonPhotocopiers(products) {
    const canonProductContainer = document.getElementById('canon-photocopier-section');
    canonProductContainer.innerHTML = products.map((item, index) => createProductHTML(item, index, 'canon')).join('');
}

// Create HTML for a photocopier
function createProductHTML(item, index, brand) {
    const { image, name, price } = item;
    const imgSrc = image ? `/static/${image}` : '/static/SPAPHOTOS/placeholder-image.png';

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
                        <label for="quantity-${brand}-${index}" style="font-weight: bold;font-size:16px; margin-right: 5px;">Quantity:</label>
                        <input 
                            type="number" 
                            id="quantity-${brand}-${index}" 
                            min="1" 
                            value="1" 
                            placeholder="1" 
                            style="width: 50px; border: 2px solid #ccc; padding: 5px; border-radius: 5px;" 
                            title="Select the quantity you want to order"
                        />
                    </div>
                </div>
                <button onclick='addToCart("${brand}", ${index})'>Add to cart</button>
            </div>
        </div>
    `;
}

// Add item to cart
function addToCart(brand, index) {
    const quantityInput = document.getElementById(`quantity-${brand}-${index}`);
    const quantity = parseInt(quantityInput.value, 10) || 1;

    let productsArray;
    switch (brand) {
        case 'hp':
            productsArray = hpPhotocopiers;
            break;
        case 'epson':
            productsArray = epsonPhotocopiers;
            break;
        case 'ricoh':
            productsArray = ricohPhotocopiers;
            break;
        case 'canon':
            productsArray = canonPhotocopiers;
            break;
        default:
            return;
    }

    const existingProductIndex = cart.findIndex(item => item.id === productsArray[index].id);
    if (existingProductIndex > -1) {
        cart[existingProductIndex].quantity += quantity;
    } else {
        cart.push({ ...productsArray[index], quantity });
    }

    displayCart();
}

// Remove item from cart
function removeFromCart(index) {
    cart.splice(index, 1);
    displayCart();
}

// Display cart
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

// Create HTML for cart item
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
// Calculate total
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
    const loadingSpinner = loading ? `<div class="spinner"></div>` : '';
    notification.innerHTML = `${loadingSpinner} ${message}`;
    notification.classList.add('show');

    setTimeout(() => {
        notification.classList.remove('show');
    }, 10000); // Hide notification after 10 seconds
}

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
    const paymentData = {
        amount: totalAmount,
        phone: formattedPhone,
        product_ids: productIds
    };

    console.log('Payment data:', paymentData); // Debugging log

    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

    // Show loading notification
    showNotification('Processing payment, please wait...', true);

    try {
        const response = await fetch('/pay', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(paymentData)
        });
        
        const contentType = response.headers.get("Content-Type");
        let result;
        if (contentType && contentType.includes("application/json")) {
            result = await response.json();
        } else {
            const text = await response.text(); // Read the response as text
            console.error('Response was not JSON:', text);
            showNotification('An unexpected error occurred. Please try again.');
            return;
        }
        
        if (response.ok) {
            handlePaymentSuccess(result);
        } else {
            handlePaymentError(result);
        }
    } catch (error) {
        showNotification('An error occurred while processing your payment. Please try again.');
        console.error('Payment error:', error);
    }
}

function handlePaymentSuccess(result) {
    setTimeout(() => {
        if (!result.pinEntered) {
            showNotification('Payment not completed: please enter the pin sent to your phone.');
        } else {
            showNotification('Payment processed, check your phone and enter pin...'); // Show notification
            cart = []; // Clear cart
            displayCart(); // Refresh the cart display
        }
    }, 10000); // Check for pin entry after 10 seconds
}

function handlePaymentError(result) {
    console.error('Payment failed response:', result);
    if (result.error === 'Insufficient balance') {
        showNotification('Payment failed due to insufficient balance.');
    } else {
        showNotification(`Payment failed: ${result.error || 'Unknown error occurred'}`);
    }
}


// Call fetch functions on page load
fetchHPPhotocopiers();
fetchEpsonPhotocopiers();
fetchRicohPhotocopiers();
fetchCanonPhotocopiers();