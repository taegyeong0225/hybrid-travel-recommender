import React from 'react';
import { Swiper, SwiperSlide } from 'swiper/react';
import { EffectCoverflow, Navigation } from 'swiper/modules';
import 'swiper/css';
import 'swiper/css/navigation';
import 'swiper/css/effect-coverflow';
import './TravelCarousel.css';

const TravelCarousel = ({ places, currentUser, handlePlaceAction }) => {
  const handleImageError = (e) => {
    if (!e.target.src.includes('/images/default.jpg')) {
      e.target.onerror = null;
      e.target.src = '/images/default.jpg';
    }
  };

  return (
    <Swiper
      effect={'coverflow'}
      grabCursor={true}
      centeredSlides={true}
      loop={true}
      slidesPerView={'auto'}
      spaceBetween={25}
      coverflowEffect={{
        rotate: 0,
        stretch: 0,
        depth: 100,
        modifier: 1,
        slideShadows: true,
      }}
      navigation={true}
      modules={[EffectCoverflow, Navigation]}
      className="travel-carousel"
    >
      {places.map((place) => (
        <SwiperSlide key={place.name} className="card">
          <img
            src={`/images/${encodeURIComponent(place.name)}.jpg`}
            alt={place.name}
            onError={handleImageError}
          />
          {currentUser && (
            <div className="card-actions">
              <button onClick={() => handlePlaceAction('/api/favorites/add', place.name)}>❤️</button>
              <button onClick={() => handlePlaceAction('/api/visited/add', place.name)}>✔️</button>
            </div>
          )}
          <div className="card-content">
            <h3>{place.name}</h3>
            <p>{place.region}</p>
            <p>⭐ {typeof place.score === "number" ? place.score.toFixed(3) : place.score}</p>
          </div>
        </SwiperSlide>
      ))}
    </Swiper>
  );
};

export default TravelCarousel;
