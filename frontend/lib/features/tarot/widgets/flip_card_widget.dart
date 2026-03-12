import 'dart:math' as math;
import 'package:flutter/material.dart';
import '../../../core/constants/colors.dart';

class FlipCardWidget extends StatefulWidget {
  const FlipCardWidget({
    super.key,
    required this.isFlipped,
    required this.isReversed,
    required this.cardName,
    required this.onTap,
  });

  final bool isFlipped;
  final bool isReversed;
  final String cardName;
  final VoidCallback onTap;

  @override
  State<FlipCardWidget> createState() => _FlipCardWidgetState();
}

class _FlipCardWidgetState extends State<FlipCardWidget>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    );
    _animation = Tween<double>(begin: 0, end: math.pi).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOutBack),
    );
  }

  @override
  void didUpdateWidget(FlipCardWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.isFlipped && !oldWidget.isFlipped) {
      _controller.forward();
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: widget.isFlipped ? null : widget.onTap,
      child: AnimatedBuilder(
        animation: _animation,
        builder: (context, child) {
          final isShowingFront = _animation.value < math.pi / 2;
          return Transform(
            alignment: Alignment.center,
            transform: Matrix4.identity()
              ..setEntry(3, 2, 0.001)
              ..rotateY(_animation.value),
            child: isShowingFront
                ? _buildCardBack()
                : Transform(
                    alignment: Alignment.center,
                    transform: Matrix4.identity()..rotateY(math.pi),
                    child: _buildCardFront(),
                  ),
          );
        },
      ),
    );
  }

  Widget _buildCardBack() {
    return Container(
      width: 90,
      height: 140,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: CosmoColors.primary, width: 1.5),
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFF1A1A3E), Color(0xFF0A0A1A)],
        ),
      ),
      child: const Center(
        child: Icon(
          Icons.auto_awesome,
          color: CosmoColors.primary,
          size: 32,
        ),
      ),
    );
  }

  Widget _buildCardFront() {
    return RotatedBox(
      quarterTurns: widget.isReversed ? 2 : 0,
      child: Container(
        width: 90,
        height: 140,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: widget.isReversed ? CosmoColors.secondary : CosmoColors.primary,
            width: 2,
          ),
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: widget.isReversed
                ? [
                    const Color(0xFF3A1A5E),
                    const Color(0xFF1A0A2E),
                  ]
                : [
                    const Color(0xFF2A1A1A),
                    const Color(0xFF1A0A0A),
                  ],
          ),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.auto_awesome,
              color: widget.isReversed
                  ? CosmoColors.secondary
                  : CosmoColors.primary,
              size: 28,
            ),
          ],
        ),
      ),
    );
  }
}
