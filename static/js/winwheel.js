var Winwheel = function (options) {
    this.canvasId = options.canvasId;
    this.numSegments = options.numSegments;
    this.outerRadius = options.outerRadius;
    this.segments = options.segments;
    this.animation = options.animation;
    this.rotationAngle = 0;
    this.isSpinning = false;
    this.ctx = document.getElementById(this.canvasId).getContext('2d');
    this.imagesLoaded = 0;

    this.preloadImages();
};

Winwheel.prototype.preloadImages = function () {
    var self = this;
    var totalImages = this.segments.length;

    this.segments.forEach(function (segment, index) {
        if (segment.image) {
            var img = new Image();
            img.onload = function () {
                segment.imgObj = img;
                self.imagesLoaded++;
                if (self.imagesLoaded === totalImages) {
                    self.draw();
                }
            };
            img.src = segment.image;
        } else {
            self.imagesLoaded++;
            if (self.imagesLoaded === totalImages) {
                self.draw();
            }
        }
    });
};

Winwheel.prototype.draw = function (ballIndex, highlightIndex) {
    var ctx = this.ctx;
    var centerX = ctx.canvas.width / 2;
    var centerY = ctx.canvas.height / 2;
    var outerRadius = this.outerRadius;
    var segAngle = 360 / this.numSegments;
    var pistaRadius = outerRadius * 0.78;
    var pistaInternaRadius = outerRadius * 0.85;
    var pistaInternaWidth = outerRadius * 0.13;
    var ballRadius = 10;

    ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);

    // Borda externa dourada
    ctx.beginPath();
    ctx.arc(centerX, centerY, outerRadius + 12, 0, 2 * Math.PI);
    ctx.fillStyle = '#FFD700';
    ctx.shadowColor = '#00eaff';
    ctx.shadowBlur = 30;
    ctx.fill();
    ctx.shadowBlur = 0;
    ctx.closePath();

    // Faixa dos números (externa)
    for (var i = 0; i < this.numSegments; i++) {
        var angle = (segAngle * i + this.rotationAngle) * Math.PI / 180;
        var nextAngle = (segAngle * (i + 1) + this.rotationAngle) * Math.PI / 180;
        ctx.beginPath();
        ctx.arc(centerX, centerY, outerRadius, angle, nextAngle, false);
        ctx.arc(centerX, centerY, outerRadius * 0.92, nextAngle, angle, true);
        ctx.closePath();
        ctx.fillStyle = (i % 2 === 0) ? "#c62828" : "#222";
        ctx.fill();
        ctx.strokeStyle = "#111";
        ctx.stroke();

        var segment = this.segments[i];
        var numeroAnimal = segment.numero || (i + 1);

        // Destaque amarelo no número sorteado
        if (typeof highlightIndex === 'number' && i === highlightIndex) {
            ctx.save();
            ctx.translate(centerX, centerY);
            ctx.rotate(angle + (nextAngle - angle) / 2);
            ctx.beginPath();
            ctx.arc(outerRadius * 0.96, 0, 28, 0, 2 * Math.PI);
            ctx.fillStyle = 'rgba(255, 215, 0, 0.7)';
            ctx.fill();
            ctx.restore();
        }

        // Número grande, centralizado na faixa
        ctx.save();
        ctx.translate(centerX, centerY);
        ctx.rotate(angle + (nextAngle - angle) / 2);
        ctx.fillStyle = "#2196f3";
        ctx.font = "bold 30px 'Arial Black', Arial, sans-serif";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(numeroAnimal, outerRadius * 0.96, 0);
        ctx.restore();
    }

    // Faixa interna (pista da bolinha, igual à externa, mas sem números)
    for (var i = 0; i < this.numSegments; i++) {
        var angle = (segAngle * i + this.rotationAngle) * Math.PI / 180;
        var nextAngle = (segAngle * (i + 1) + this.rotationAngle) * Math.PI / 180;
        ctx.beginPath();
        ctx.arc(centerX, centerY, pistaInternaRadius, angle, nextAngle, false);
        ctx.arc(centerX, centerY, pistaInternaRadius - pistaInternaWidth, nextAngle, angle, true);
        ctx.closePath();
        ctx.fillStyle = (i % 2 === 0) ? "#c62828" : "#222";
        ctx.fill();
        ctx.strokeStyle = "#111";
        ctx.stroke();
    }

    // Centro preto
    ctx.beginPath();
    ctx.arc(centerX, centerY, pistaRadius * 0.7, 0, 2 * Math.PI);
    ctx.fillStyle = '#181818';
    ctx.fill();
    ctx.closePath();

    // Bolinha pulando de setor em setor
    if (typeof ballIndex === 'number') {
        var angle = (segAngle * ballIndex + this.rotationAngle + segAngle / 2) * Math.PI / 180;
        var ballX = centerX + pistaInternaRadius * Math.cos(angle);
        var ballY = centerY + pistaInternaRadius * Math.sin(angle);
        ctx.beginPath();
        ctx.arc(ballX, ballY, ballRadius, 0, 2 * Math.PI);
        ctx.fillStyle = '#fff';
        ctx.shadowColor = '#888';
        ctx.shadowBlur = 8;
        ctx.fill();
        ctx.shadowBlur = 0;
        ctx.closePath();
    }
};

Winwheel.prototype.startAnimation = function () {
    if (this.isSpinning) return;
    this.isSpinning = true;
    var totalRotation = (this.animation.spins || 8) * 360 + Math.floor(Math.random() * 360);
    var duration = (this.animation.duration || 6) * 1000;
    var startTime = null;
    var self = this;

    function animate(timestamp) {
        if (!startTime) startTime = timestamp;
        var progress = timestamp - startTime;
        var percent = Math.min(progress / duration, 1);
        var easeOut = (--percent) * percent * percent + 1;
        self.rotationAngle = (totalRotation * easeOut) % 360;
        self.draw();
        if (percent < 1) {
            requestAnimationFrame(animate);
        } else {
            self.isSpinning = false;
            if (self.animation.callbackFinished) {
                self.animation.callbackFinished();
            }
        }
    }
    requestAnimationFrame(animate);
};

Winwheel.prototype.animateWithBall = function (targetIndex, callback) {
    var self = this;
    var segAngle = 360 / this.numSegments;
    var totalSpins = 8;
    var duration = 7000;
    var startTime = null;
    var startRotation = this.rotationAngle;
    var endRotation = (360 * totalSpins) + (360 - targetIndex * segAngle - segAngle / 2);
    var pistaRadius = this.outerRadius * 0.78;
    var ballStartAngle = Math.PI / 2;
    var ballEndAngle = ((360 - targetIndex * segAngle - segAngle / 2) * Math.PI / 180) + Math.PI / 2;

    function animate(timestamp) {
        if (!startTime) startTime = timestamp;
        var progress = Math.min((timestamp - startTime) / duration, 1);
        var easeOut = (--progress) * progress * progress + 1;
        var currentRotation = startRotation + (endRotation - startRotation) * easeOut;
        self.rotationAngle = currentRotation % 360;
        var ballAngle = ballStartAngle + (ballEndAngle - ballStartAngle) * easeOut;
        self.draw(ballAngle, (progress === 1 ? targetIndex : undefined));
        if (progress < 1) {
            requestAnimationFrame(animate);
        } else {
            self.isSpinning = false;
            self.draw(ballEndAngle, targetIndex);
            if (callback) callback();
        }
    }
    this.isSpinning = true;
    requestAnimationFrame(animate);
};

Winwheel.prototype.getIndicatedSegment = function () {
    var segAngle = 360 / this.numSegments;
    var currentRotation = (360 - (this.rotationAngle % 360)) % 360;
    var index = Math.floor(currentRotation / segAngle);
    return this.segments[index];
};

