let cart = [];
let quartetProducts = [];
let expoProducts = [];
let ghentProducts = [];
let lorellProducts = [];
let mastervisionProducts = [];
let officemateProducts = [];
let rubbermaidProducts = [];
let zononProducts = [];
let biSilqueProducts = [];
let threeMProducts = [];

async function fetchQuartetProducts() {
    try {
        const response = await fetch('/api/whiteboard-quartet');
        quartetProducts = await response.json();
        displayQuartetProducts(quartetProducts);
    } catch (error) {
        console.error('Error fetching Quartet products:', error);
    }
}

async function fetchExpoProducts() {
    try {
        const response = await fetch('/api/whiteboard-expo');
        expoProducts = await response.json();
        displayExpoProducts(expoProducts);
    } catch (error) {
        console.error('Error fetching Expo products:', error);
    }
}

async function fetchGhentProducts() {
    try {
        const response = await fetch('/api/whiteboard-ghent');
        ghentProducts = await response.json();
        displayGhentProducts(ghentProducts);
    } catch (error) {
        console.error('Error fetching Ghent products:', error);
    }
}

async function fetchLorellProducts() {
    try {
        const response = await fetch('/api/whiteboard-lorell');
        lorellProducts = await response.json();
        displayLorellProducts(lorellProducts);
    } catch (error) {
        console.error('Error fetching Lorell products:', error);
    }
}

async function fetchMasterVisionProducts() {
    try {
        const response = await fetch('/api/whiteboard-mastervision');
        mastervisionProducts = await response.json();
        displayMasterVisionProducts(mastervisionProducts);
    } catch (error) {
        console.error('Error fetching MasterVision products:', error);
    }
}

async function fetchOfficemateProducts() {
    try {
        const response = await fetch('/api/whiteboard-officemate');
        officemateProducts = await response.json();
        displayOfficemateProducts(officemateProducts);
    } catch (error) {
        console.error('Error fetching Officemate products:', error);
    }
}

async function fetchRubbermaidProducts() {
    try {
        const response = await fetch('/api/whiteboard-rubbermaid');
        rubbermaidProducts = await response.json();
        displayRubbermaidProducts(rubbermaidProducts);
    } catch (error) {
        console.error('Error fetching Rubbermaid products:', error);
    }
}

async function fetchZononProducts() {
    try {
        const response = await fetch('/api/whiteboard-zonon');
        zononProducts = await response.json();
        displayZononProducts(zononProducts);
    } catch (error) {
        console.error('Error fetching Zonon products:', error);
    }
}

async function fetchBiSilqueProducts() {
    try {
        const response = await fetch('/api/whiteboard-bi-silque');
        biSilqueProducts = await response.json();
        displayBiSilqueProducts(biSilqueProducts);
    } catch (error) {
        console.error('Error fetching Bi-silque products:', error);
    }
}

async function fetchThreeMProducts() {
    try {
        const response = await fetch('/api/whiteboard-3m');
        threeMProducts = await response.json();
        displayThreeMProducts(threeMProducts);
    } catch (error) {
        console.error('Error fetching 3M products:', error);
    }
}

function displayQuartetProducts(products) {
    const quartetProductContainer = document.getElementById('quartet-whiteboard-section');
    quartetProductContainer.innerHTML = products.map((item, index) => createProductHTML(item, index, 'quartet')).join('');
}

function displayExpoProducts(products) {
    const expoProductContainer = document.getElementById('expo-whiteboard-section');
    expoProductContainer.innerHTML = products.map((item, index) => createProductHTML(item, index, 'expo')).join('');
}

function displayGhentProducts(products) {
    const ghentProductContainer = document.getElementById('ghent-whiteboard-section');
    ghentProductContainer.innerHTML = products.map((item, index) => createProductHTML(item, index, 'ghent')).join('');
}

function displayLorellProducts(products) {
    const lorellProductContainer = document.getElementById('lorell-whiteboard-section');
    lorellProductContainer.innerHTML = products.map((item, index) => createProductHTML(item, index, 'lorell')).join('');
}

function displayMasterVisionProducts(products) {
    const masterVisionProductContainer = document.getElementById('mastervision-whiteboard-section');
    masterVisionProductContainer.innerHTML = products.map((item, index) => createProductHTML(item, index, 'mastervision')).join('');
}

function displayOfficemateProducts(products) {
    const officemateProductContainer = document.getElementById('officemate-whiteboard-section');
    officemateProductContainer.innerHTML = products.map((item, index) => createProductHTML(item, index, 'officemate')).join('');
}

function displayRubbermaidProducts(products) {
    const rubbermaidProductContainer = document.getElementById('rubbermaid-whiteboard-section');
    rubbermaidProductContainer.innerHTML = products.map((item, index) => createProductHTML(item, index, 'rubbermaid')).join('');
}

function displayZononProducts(products) {
    const zononProductContainer = document.getElementById('zonon-whiteboard-section');
    zononProductContainer.innerHTML = products.map((item, index) => createProductHTML(item, index, 'zonon')).join('');
}

function displayBiSilqueProducts(products) {
    const biSilqueProductContainer = document.getElementById('bi-silque-whiteboard-section');
    biSilqueProductContainer.innerHTML = products.map((item, index) => createProductHTML(item, index, 'bi-silque')).join('');
}

function displayThreeMProducts(products) {
    const threeMProductContainer = document.getElementById('threeM-whiteboard-section');
    threeMProductContainer.innerHTML = products.map((item, index) => createProductHTML(item, index, '3M')).join('');
}

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

function addToCart(brand, index) {
    const quantityInput = document.getElementById(`quantity-${brand}-${index}`);
    const quantity = parseInt(quantityInput.value, 10) || 1;

    let productsArray;
    switch (brand) {
        case 'quartet':
            productsArray = quartetProducts;
            break;
        case 'expo':
            productsArray = expoProducts;
            break;
        case 'ghent':
            productsArray = ghentProducts;
            break;
        case 'lorell':
            productsArray = lorellProducts;
            break;
        case 'mastervision':
            productsArray = mastervisionProducts;
            break;
        case 'officemate':
            productsArray = officemateProducts;
            break;
        case 'rubbermaid':
            productsArray = rubbermaidProducts;
            break;
        case 'zonon':
            productsArray = zononProducts;
            break;
        case 'bi-silque':
            productsArray = biSilqueProducts;
            break;
        case '3M':
            productsArray = threeMProducts;
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
fetchQuartetProducts();
fetchExpoProducts();
fetchGhentProducts();
fetchLorellProducts();
fetchMasterVisionProducts();
fetchOfficemateProducts();
fetchRubbermaidProducts();
fetchZononProducts();
fetchBiSilqueProducts();
fetchThreeMProducts();
