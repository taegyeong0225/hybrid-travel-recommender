import React, { useState } from 'react';
import { Swiper, SwiperSlide } from 'swiper/react';
import { EffectCoverflow, Navigation } from 'swiper/modules';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faBookmark as faBookmarkSolid, faCircleCheck as faCircleCheckSolid } from '@fortawesome/free-solid-svg-icons';
import { faBookmark as faBookmarkRegular, faCircle } from '@fortawesome/free-regular-svg-icons';
import 'swiper/css';
import 'swiper/css/navigation';
import 'swiper/css/effect-coverflow';
import './TravelCarousel.css';

const TravelCarousel = ({ places, currentUser, handlePlaceAction }) => {
  const [bookmarkedPlaces, setBookmarkedPlaces] = useState(new Set());
  const [checkedInPlaces, setCheckedInPlaces] = useState(new Set());

  const handleImageError = (e) => {
    if (!e.target.src.includes('/images/default.jpg')) {
      e.target.onerror = null;
      e.target.src = '/images/default.jpg';
    }
  };

  const handleBookmark = (placeName) => {
    setBookmarkedPlaces(prev => {
      const newSet = new Set(prev);
      if (newSet.has(placeName)) {
        newSet.delete(placeName);
      } else {
        newSet.add(placeName);
      }
      return newSet;
    });
    handlePlaceAction('/api/favorites/add', placeName);
  };

  const handleCheckIn = (placeName) => {
    setCheckedInPlaces(prev => {
      const newSet = new Set(prev);
      if (newSet.has(placeName)) {
        newSet.delete(placeName);
      } else {
        newSet.add(placeName);
      }
      return newSet;
    });
    handlePlaceAction('/api/visited/add', placeName);
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
              <button
                className={`bookmark-btn ${bookmarkedPlaces.has(place.name) ? 'active' : ''}`}
                onClick={() => handleBookmark(place.name)}
                title="찜하기"
              >
                <FontAwesomeIcon
                  icon={bookmarkedPlaces.has(place.name) ? faBookmarkSolid : faBookmarkRegular}
                />
              </button>
              <button
                className={`checkin-btn ${checkedInPlaces.has(place.name) ? 'active' : ''}`}
                onClick={() => handleCheckIn(place.name)}
                title="체크인"
              >
                <FontAwesomeIcon
                  icon={checkedInPlaces.has(place.name) ? faCircleCheckSolid : faCircle}
                />
              </button>
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
