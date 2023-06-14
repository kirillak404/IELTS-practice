// Find all rating items
const ratings = document.querySelectorAll(".rating");

// Iterate over all rating items
ratings.forEach((rating, index) => {
// Get content and get score as an int
const ratingContent = rating.textContent;
const ratingScore = parseInt(ratingContent, 10);

// Define if the score is good, meh or bad according to its value
const scoreClass =
 ratingScore < 6 ? "bad" : ratingScore < 8 ? "meh" : "good";

// Add score class to the rating
rating.classList.add(scoreClass);

// After adding the class, get its color
const ratingColor = window.getComputedStyle(rating).backgroundColor;

// Define the background gradient according to the score and color
const gradientPercentage = (ratingScore / 9) * 100; // Calculate the percentage based on 9 scale score
const gradient = `background: conic-gradient(${ratingColor} ${gradientPercentage}%, var(--rating-color-background) ${gradientPercentage}% 100%)`;

// Set the gradient as the rating background
rating.setAttribute("style", gradient);

// Find the corresponding score text element
const scoreElement = rating.nextElementSibling.querySelector('.score-text');

// Update the score text
scoreElement.textContent = `Your score is ${ratingScore}/9`;

// Update the color of the score text
scoreElement.style.color = ratingColor;

// Wrap the content in a tag to show it above the pseudo element that masks the bar
rating.innerHTML = `<span>${ratingScore}</span>`;
});


// Mouseover pron errors
$(document).ready(function() {
    $('.error').on('mouseenter', function(e) {
        $('.toast').stop();
        var top = e.pageY;
        var left = e.pageX;

        $('.toast').css({top: (top - $('.toast').height() - 10) + 'px', left: (left + 10) + 'px'});

        var errorType = $(this).data('error-type').charAt(0).toUpperCase() + $(this).data('error-type').slice(1);
        $('.toast-header strong').html(errorType);

        var accuracy = '';
        if ($(this).data('accuracy-score')) {
            accuracy = '<b>Score: </b>' + $(this).data('accuracy-score') + '<br>';
        }

        var explanation = '<b>Description: </b>' + $(this).data('error-long-description');
        $('.toast-body').html(accuracy + ' ' + ' ' + explanation);

        $('.toast').fadeIn(250);
    });

    $('.error').on('mouseleave', function() {
        $('.toast').fadeOut(250);
    });
});


// Tooltips on mouseover
$(function () {
 $('[data-toggle="tooltip"]').tooltip()
})