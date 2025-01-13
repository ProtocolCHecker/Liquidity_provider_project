// async function fetchTokenHolders() {
//     const response = await fetch('/Users/barguesflorian/Documents/LP_project/token_holders.json');
//     const tokenHolders = await response.json();

//     const totalSupply = tokenHolders.reduce((total, holder) => total + holder.balance, 0);

//     drawBubbleMap(tokenHolders, totalSupply);
// }

// function drawBubbleMap(tokenHolders, totalSupply) {
//     const width = 800;
//     const height = 600;

//     const svg = d3.select('#map')
//         .append('svg')
//         .attr('width', width)
//         .attr('height', height);

//     const bubbles = svg.selectAll('circle')
//         .data(tokenHolders)
//         .enter()
//         .append('circle')
//         .attr('cx', (d, i) => (i + 1) * (width / (tokenHolders.length + 1)))
//         .attr('cy', height / 2)
//         .attr('r', d => Math.sqrt(d.balance) * 500000) // Scale the radius based on balance (adjust multiplier as needed)
//         .style('fill', 'blue')
//         .style('opacity', 0.7)
//         .on('mouseover', function(event, d) {
//             d3.select(this).style('fill', 'orange');
//             // Show tooltip with address and balance
//             d3.select('#tooltip')
//                 .style('opacity', 1)
//                 .html(`Address: ${d.address}<br/>Balance: ${d.balance}`)
//                 .style('left', `${event.pageX}px`)
//                 .style('top', `${event.pageY}px`);
//         })
//         .on('mouseout', function() {
//             d3.select(this).style('fill', 'blue');
//             d3.select('#tooltip').style('opacity', 0);
//         });

//     // Ranking list
//     const rankingList = d3.select('#ranking-list');
//     tokenHolders.forEach(holder => {
//         rankingList.append('li').text(`${holder.address}: ${holder.percentage.toFixed(2)}%`);
//     });
// }

// // Set current date
// document.getElementById('current-date').innerText = new Date().toLocaleString();

// // Fetch and draw bubble map on page load
// fetchTokenHolders();


async function fetchTokenHolders() {
    try {
        const response = await fetch('/Users/barguesflorian/Documents/LP_project/token_holders.json'); // Use a relative path or serve the file from a web server
        const tokenHolders = await response.json();

        const totalSupply = tokenHolders.reduce((total, holder) => total + holder.balance, 0);

        drawBubbleMap(tokenHolders, totalSupply);
    } catch (error) {
        console.error('Error fetching token holders:', error);
    }
}

function drawBubbleMap(tokenHolders, totalSupply) {
    const width = 800;
    const height = 600;

    const svg = d3.select('#map')
        .append('svg')
        .attr('width', width)
        .attr('height', height);

    const bubbles = svg.selectAll('circle')
        .data(tokenHolders)
        .enter()
        .append('circle')
        .attr('cx', (d, i) => (i + 1) * (width / (tokenHolders.length + 1)))
        .attr('cy', height / 2)
        .attr('r', d => Math.sqrt(d.balance) * 500000) // Adjust the multiplier as needed
        .style('fill', 'blue')
        .style('opacity', 0.7)
        .on('mouseover', function(event, d) {
            d3.select(this).style('fill', 'orange');
            d3.select('#tooltip')
                .style('opacity', 1)
                .html(`Address: ${d.address}<br/>Balance: ${d.balance}`)
                .style('left', `${event.pageX}px`)
                .style('top', `${event.pageY}px`);
        })
        .on('mouseout', function() {
            d3.select(this).style('fill', 'blue');
            d3.select('#tooltip').style('opacity', 0);
        });

    const rankingList = d3.select('#ranking-list');
    tokenHolders.forEach(holder => {
        rankingList.append('li').text(`${holder.address}: ${holder.percentage.toFixed(2)}%`);
    });
}

document.getElementById('current-date').innerText = new Date().toLocaleString();

fetchTokenHolders();
