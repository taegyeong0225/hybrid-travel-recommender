import React, { useState, useEffect } from 'react';
import { Swiper, SwiperSlide } from 'swiper/react';
import { EffectCoverflow, Navigation } from 'swiper/modules';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faBookmark as faBookmarkSolid, faCircleCheck as faCircleCheckSolid, faSearch, faMountain, faHotel, faUtensils, faCalendarDays, faShoppingBag, faCar, faStar, faPlane } from '@fortawesome/free-solid-svg-icons';
import { faBookmark as faBookmarkRegular, faCircle } from '@fortawesome/free-regular-svg-icons';
import 'swiper/css';
import 'swiper/css/navigation';
import 'swiper/css/effect-coverflow';
import './TravelCarousel.css';

// 메인 타이틀 컴포넌트
const MainTitle = () => {
  return (
    <div className="main-title">
      <h2>
        오늘의 추천 여행지
        <span className="title-icon"><FontAwesomeIcon icon={faPlane} /></span>
      </h2>
    </div>
  );
};

// 검색창 컴포넌트
const SearchBar = () => {
  return (
    <div className="search-bar-container">
      <div className="search-bar">
        <input type="text" placeholder="가고 싶은 / 다녀온 여행지를 입력하세요" />
        <button>
          <FontAwesomeIcon icon={faSearch} />
        </button>
      </div>
    </div>
  );
};

// 해시태그 컴포넌트
const HashtagSection = () => {
  const hashtags = ['#단기 소수 여행객', '#장기 단체여행객', '#균형잡힌 일반 여행객'];

  return (
    <div className="hashtag-section">
      {hashtags.map((tag, index) => (
        <button key={index} className="hashtag-btn">
          {tag}
        </button>
      ))}
    </div>
  );
};

// Quick Menu 컴포넌트
const QuickMenu = () => {
  const menuItems = [
    { icon: faStar, label: '추천' },
    { icon: faCalendarDays, label: '축제' },
    { icon: faUtensils, label: '음식점' },
    { icon: faHotel, label: '숙박' },
    { icon: faShoppingBag, label: '쇼핑' }
  ];

  return (
    <div className="quick-menu">
      <div className="quick-menu-title">Quick Menu</div>
      <div className="quick-menu-items">
        {menuItems.map((item, index) => (
          <button key={index} className="quick-menu-item">
            <FontAwesomeIcon icon={item.icon} />
            <span>{item.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
};


const TravelCarousel = ({ places, currentUser, handlePlaceAction, userFavorites = [], userVisited = [] }) => {
  const [bookmarkedPlaces, setBookmarkedPlaces] = useState(new Set());
  const [checkedInPlaces, setCheckedInPlaces] = useState(new Set());

  // userFavorites/userVisited가 변경되면 상태 업데이트
  useEffect(() => {
    if (userFavorites.length > 0 || userVisited.length > 0) {
      // poi_id로 저장되어 있으므로, place.poi_id와 비교
      const favSet = new Set();
      const visitSet = new Set();

      places.forEach(place => {
        const placeId = place.poi_id || place.name;
        if (userFavorites.includes(placeId)) {
          favSet.add(place.name);
        }
        if (userVisited.includes(placeId)) {
          visitSet.add(place.name);
        }
      });

      setBookmarkedPlaces(favSet);
      setCheckedInPlaces(visitSet);
    }
  }, [userFavorites, userVisited, places]);

  const handleImageError = (e) => {
    if (!e.target.src.includes('/images/default.jpg')) {
      e.target.onerror = null;
      e.target.src = '/images/default.jpg';
    }
  };

  const handleBookmark = (place) => {
    setBookmarkedPlaces(prev => {
      const newSet = new Set(prev);
      if (newSet.has(place.name)) {
        newSet.delete(place.name);
      } else {
        newSet.add(place.name);
      }
      return newSet;
    });
    handlePlaceAction('/api/favorites/add', place.poi_id || place.name);
  };

  const handleCheckIn = (place) => {
    setCheckedInPlaces(prev => {
      const newSet = new Set(prev);
      if (newSet.has(place.name)) {
        newSet.delete(place.name);
      } else {
        newSet.add(place.name);
      }
      return newSet;
    });
    handlePlaceAction('/api/visited/add', place.poi_id || place.name);
  };

  return (
    <div className="carousel-container">
      <MainTitle />
      <SearchBar />
      <HashtagSection />
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
              src={
                place.image_url
                  ? (place.image_url.startsWith('http')
                    ? place.image_url  // 외부 URL (한국관광공사 API)
                    : `http://localhost:8000${place.image_url}`)  // 내부 static 파일
                  : `/images/${encodeURIComponent(place.name)}.jpg`  // fallback
              }
              alt={place.name}
              onError={handleImageError}
            />
            {currentUser && (
              <div className="card-actions">
                <button
                  className={`bookmark-btn ${bookmarkedPlaces.has(place.name) ? 'active' : ''}`}
                  onClick={() => handleBookmark(place)}
                  title="찜하기"
                >
                  <FontAwesomeIcon
                    icon={bookmarkedPlaces.has(place.name) ? faBookmarkSolid : faBookmarkRegular}
                  />
                </button>
                <button
                  className={`checkin-btn ${checkedInPlaces.has(place.name) ? 'active' : ''}`}
                  onClick={() => handleCheckIn(place)}
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
              {/* <p>⭐ {typeof place.score === "number" ? place.score.toFixed(3) : place.score}</p> */}
            </div>
          </SwiperSlide>
        ))}
      </Swiper>
      <QuickMenu />
    </div>
  );
};

export default TravelCarousel;
