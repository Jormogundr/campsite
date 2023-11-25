document.addEventListener("DOMContentLoaded", () => {
  // 1 star rating
  $("#star_0").click(function () {
    $("#star_0").attr("src", "/static/images/star_filled.png");
    $("#star_1").attr("src", "/static/images/star_empty.png");
    $("#star_2").attr("src", "/static/images/star_empty.png");
    $("#star_3").attr("src", "/static/images/star_empty.png");
    $("#star_4").attr("src", "/static/images/star_empty.png");
    $("#rating_content").attr("value", "1");
  });

  // 2 star rating
  $("#star_1").click(function () {
    $("#star_0").attr("src", "/static/images/star_filled.png");
    $("#star_1").attr("src", "/static/images/star_filled.png");
    $("#star_2").attr("src", "/static/images/star_empty.png");
    $("#star_3").attr("src", "/static/images/star_empty.png");
    $("#star_4").attr("src", "/static/images/star_empty.png");
    $("#rating_content").attr("value", "2");
  });

  // 3 star rating
  $("#star_2").click(function () {
    $("#star_0").attr("src", "/static/images/star_filled.png");
    $("#star_1").attr("src", "/static/images/star_filled.png");
    $("#star_2").attr("src", "/static/images/star_filled.png");
    $("#star_3").attr("src", "/static/images/star_empty.png");
    $("#star_4").attr("src", "/static/images/star_empty.png");
    $("#rating_content").attr("value", "3");
  });

  // 4 star rating
  $("#star_3").click(function () {
    $("#star_0").attr("src", "/static/images/star_filled.png");
    $("#star_1").attr("src", "/static/images/star_filled.png");
    $("#star_2").attr("src", "/static/images/star_filled.png");
    $("#star_3").attr("src", "/static/images/star_filled.png");
    $("#star_4").attr("src", "/static/images/star_empty.png");
    $("#rating_content").attr("value", "4");
  });

  // 5 star rating
  $("#star_4").click(function () {
    $("#star_0").attr("src", "/static/images/star_filled.png");
    $("#star_1").attr("src", "/static/images/star_filled.png");
    $("#star_2").attr("src", "/static/images/star_filled.png");
    $("#star_3").attr("src", "/static/images/star_filled.png");
    $("#star_4").attr("src", "/static/images/star_filled.png");
    $("#rating_content").attr("value", "5");
  });
});
