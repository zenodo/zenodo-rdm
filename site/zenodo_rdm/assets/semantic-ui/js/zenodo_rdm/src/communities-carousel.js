document.addEventListener("DOMContentLoaded", () => initCommunityCarousel());

function initCommunityCarousel() {
  const carousel = document.getElementById("communities-carousel");
  const slidesContainer = document.getElementById("carousel-slides");
  const carouselSlides = slidesContainer.querySelectorAll(".item.slide");
  const prevSlideBtn = document.getElementById("prev-slide-btn");
  const nextSlideBtn = document.getElementById("next-slide-btn");

  const animationSpeed = parseInt(carousel.dataset.animationSpeed);
  const intervalDelay = parseInt(carousel.dataset.intervalDelay);

  const numSlides = carouselSlides.length;
  const slideWidth = carouselSlides[0].offsetWidth;

  const minIndex = 0;
  const maxIndex = numSlides - 1;
  var activeIndex = 0;

  var transitionCompleted = true;

  carouselSlides.forEach((slide, index) => {
    // Remove all inactive slides from the DOM.
    if (index !== activeIndex) slide.remove();
  });

  /**
   * Switches carousel slide
   * @param {string} direction Direction to slide - left or right
   */
  const slide = (direction) => {
    const currentSlide = slidesContainer.querySelector(".item.slide");
    const slideLeft = direction === "left";

    if (transitionCompleted) {
      transitionCompleted = false;
      const prevVisibleIndex = slideLeft ? 0 : 1;
      const currentVisibleIndex = slideLeft ? 1 : 0;
      const slideAmount = -slideWidth;

      if (direction === "left") {
        activeIndex++;
        if (activeIndex > maxIndex) {
          activeIndex = minIndex;
        }

        // Add active slide after currently visible slide
        currentSlide.after(carouselSlides[activeIndex]);

        // Translate the slides-container such that the active slide comes to center.
        slidesContainer.style.transitionDuration = `${animationSpeed}ms`;
        slidesContainer.style.transform = `translateX(${slideAmount}px)`;
      } else {
        activeIndex--;
        if (activeIndex < minIndex) {
          activeIndex = maxIndex;
        }

        // Add active slide before currently visible slide
        currentSlide.before(carouselSlides[activeIndex]);

        // Translate the slides-container such that the previously active slide stays in center.
        slidesContainer.style.transition = "transform .001ms";
        slidesContainer.style.transform = `translateX(${slideAmount}px)`;
      }

      const currentSlides = slidesContainer.querySelectorAll(".item.slide");

      // Control slide visibility by adding/removing classes
      currentSlides[prevVisibleIndex].classList.remove("visible");
      currentSlides[prevVisibleIndex].classList.add("hidden");

      currentSlides[currentVisibleIndex].classList.add("visible");
      currentSlides[currentVisibleIndex].classList.remove("hidden");

      // Transition-end event handler, runs once when slides-container transition is finished
      const transitionEndHandler = (direction) => {
        if (direction === "left") {
          // Tranlate the slides-container such that the active item will be
          // in center once the previously active item is removed, then remove that item
          slidesContainer.style.transitionDuration = "0s";
          slidesContainer.style.transform = "translateX(0px)";
          currentSlides[prevVisibleIndex].remove();
        } else {
          const removePreviousSlide = () => {
            currentSlides[prevVisibleIndex].remove();
            slidesContainer.removeEventListener("transitionend", removePreviousSlide);
          };

          // Remove previous slide once the second transition is completed
          slidesContainer.addEventListener("transitionend", removePreviousSlide, {
            once: true,
          });

          // Translate slides-container to center
          slidesContainer.style.transitionDuration = `${animationSpeed}ms`;
          slidesContainer.style.transform = "translateX(0px)";
        }

        transitionCompleted = true;
        slidesContainer.removeEventListener("transitionend", transitionEndHandler);
      };

      slidesContainer.addEventListener(
        "transitionend",
        () => transitionEndHandler(direction),
        { once: true }
      );
    }
  };

  // Run carousel automatically on page load
  const setCarouselTimer = () => setInterval(() => slide("left"), intervalDelay);
  var carouselTimer = setCarouselTimer();

  // Pause carousel on focus
  carousel.addEventListener("focusin", () => {
    clearInterval(carouselTimer);
  });
  carousel.addEventListener("focusout", () => {
    carouselTimer = setCarouselTimer();
  });

  // Navigation arrow event handlers
  prevSlideBtn.addEventListener("click", () => slide("right"));
  prevSlideBtn.addEventListener("keydown", (event) => {
    event.key === "Enter" && slide("right");
  });

  nextSlideBtn.addEventListener("click", () => slide("left"));
  nextSlideBtn.addEventListener("keydown", (event) => {
    event.key === "Enter" && slide("left");
  });
}
