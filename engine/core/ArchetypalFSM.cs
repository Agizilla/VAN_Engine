using System;
using System.Collections.Generic;

namespace VAN_Engine.Core
{
    /// <summary>
    /// ISO_011: Archetypal Finite State Machine with non-linear Quaternion Coupling.
    /// Manages creative orchestration and pipeline state trajectory using deterministic geometric boundaries.
    /// </summary>
    public enum TarotPosition
    {
        Past = 0,      // S0: Initial Baseline Conditions
        Present = 1,   // S_active: Current Active Execution Context
        Obstacle = 2,  // S_filter: High-Impedance Boundary Inversion Filter
        Potential = 3  // S_n+1: Target State Optimization Path
    }

    public enum MajorArcana
    {
        TheFool = 0, TheMagician = 1, TheHighPriestess = 2, TheEmpress = 3,
        TheEmperor = 4, TheHierophant = 5, TheLovers = 6, TheChariot = 7,
        Strength = 8, TheHermit = 9, WheelOfFortune = 10, Justice = 11,
        TheHangedMan = 12, Death = 13, Temperance = 14, TheDevil = 15,
        TheTower = 16, TheStar = 17, TheMoon = 18, TheSun = 19,
        Judgement = 20, TheWorld = 21
    }

    public struct AstrologicalTransit
    {
        public double W_modifier { get; set; } // Sound-Shape modulation factor
        public double X_modifier { get; set; } // Sound-Number modulation factor
        public double Y_modifier { get; set; } // Shape-Time modulation factor
        public double Z_modifier { get; set; } // Number-Time modulation factor

        public static AstrologicalTransit Identity => new AstrologicalTransit { W_modifier = 1.0, X_modifier = 1.0, Y_modifier = 1.0, Z_modifier = 1.0 };
    }

    public class ArchetypalState
    {
        public MajorArcana Archetype { get; }
        public IsographicQuaternion BaseQuaternion { get; }

        public ArchetypalState(MajorArcana archetype, IsographicQuaternion baseQuat)
        {
            Archetype = archetype;
            BaseQuaternion = baseQuat;
        }
    }

    public class ArchetypalFSM
    {
        private readonly Dictionary<TarotPosition, ArchetypalState> _pipelineSpread;
        private readonly double _tolerance = 1e-6;

        public ArchetypalFSM(ArchetypalState past, ArchetypalState present, ArchetypalState obstacle, ArchetypalState potential)
        {
            _pipelineSpread = new Dictionary<TarotPosition, ArchetypalState>
            {
                { TarotPosition.Past, past },
                { TarotPosition.Present, present },
                { TarotPosition.Obstacle, obstacle },
                { TarotPosition.Potential, potential }
            };
        }

        /// <summary>
        /// Executes a single pipeline step transitioning from the Present state through the Obstacle filter 
        /// toward the Target Potential, modulated by structural Astrological transits.
        /// </summary>
        public IsographicQuaternion Transition(AstrologicalTransit transit)
        {
            IsographicQuaternion presentQuat = _pipelineSpread[TarotPosition.Present].BaseQuaternion;
            IsographicQuaternion obstacleQuat = _pipelineSpread[TarotPosition.Obstacle].BaseQuaternion;
            IsographicQuaternion potentialQuat = _pipelineSpread[TarotPosition.Potential].BaseQuaternion;

            // 1. Apply Astrological transit as a dimension-specific field filter
            IsographicQuaternion modulatedPresent = ApplyTransit(presentQuat, transit);

            // 2. Intersect with the high-impedance inversion filter (The Obstacle) via quaternion multiplication
            // This couples the dimensions dynamically instead of processing isolated linear coordinates.
            IsographicQuaternion filteredContext = Multiply(modulatedPresent, obstacleQuat);

            // 3. Compute Spherical Linear Interpolation (Slerp) toward the target potential
            // This ensures smooth vector trajectory navigation inside the 4D index
            double interpolationFactor = CalculateInterpolationFactor(filteredContext, potentialQuat);
            IsographicQuaternion nextTargetState = Slerp(filteredContext, potentialQuat, interpolationFactor);

            // 4. Invariance Guard: Enforce global field magnitude validation contract
            AssertInvarianceGuard(nextTargetState);

            return nextTargetState;
        }

        private IsographicQuaternion ApplyTransit(IsographicQuaternion quat, AstrologicalTransit transit)
        {
            return new IsographicQuaternion
            {
                W = quat.W * transit.W_modifier,
                X = quat.X * transit.X_modifier,
                Y = quat.Y * transit.Y_modifier,
                Z = quat.Z * transit.Z_modifier
            };
        }

        private IsographicQuaternion Multiply(IsographicQuaternion q1, IsographicQuaternion q2)
        {
            return new IsographicQuaternion
            {
                W = q1.W * q2.W - q1.X * q2.X - q1.Y * q2.Y - q1.Z * q2.Z,
                X = q1.W * q2.X + q1.X * q2.W + q1.Y * q2.Z - q1.Z * q2.Y,
                Y = q1.W * q2.Y - q1.X * q2.Z + q1.Y * q2.W + q1.Z * q2.X,
                Z = q1.W * q2.Z + q1.X * q2.Y - q1.Y * q2.X + q1.Z * q2.W
            };
        }

        private double CalculateInterpolationFactor(IsographicQuaternion current, IsographicQuaternion target)
        {
            // Compute structural alignment using 4D dot product bounds
            double dot = current.W * target.W + current.X * target.X + current.Y * target.Y + current.Z * target.Z;
            return Math.Min(1.0, Math.Max(0.0, Math.Abs(dot))); 
        }

        private IsographicQuaternion Slerp(IsographicQuaternion q1, IsographicQuaternion q2, double t)
        {
            double dot = q1.W * q2.W + q1.X * q2.X + q1.Y * q2.Y + q1.Z * q2.Z;

            if (dot < 0.0)
            {
                q2 = new IsographicQuaternion { W = -q2.W, X = -q2.X, Y = -q2.Y, Z = -q2.Z };
                dot = -dot;
            }

            if (dot > 0.9995)
            {
                // Linear interpolation fallback for close vectors to prevent division by zero
                var result = new IsographicQuaternion
                {
                    W = q1.W + t * (q2.W - q1.W),
                    X = q1.X + t * (q2.X - q1.X),
                    Y = q1.Y + t * (q2.Y - q1.Y),
                    Z = q1.Z + t * (q2.Z - q1.Z)
                };
                return Normalize(result);
            }

            double theta_0 = Math.Acos(dot);
            double theta = theta_0 * t;
            double sin_theta = Math.Sin(theta);
            double sin_theta_0 = Math.Sin(theta_0);

            double s0 = Math.Cos(theta) - dot * sin_theta / sin_theta_0;
            double s1 = sin_theta / sin_theta_0;

            return new IsographicQuaternion
            {
                W = (s0 * q1.W) + (s1 * q2.W),
                X = (s0 * q1.X) + (s1 * q2.X),
                Y = (s0 * q1.Y) + (s1 * q2.Y),
                Z = (s0 * q1.Z) + (s1 * q2.Z)
            };
        }

        private IsographicQuaternion Normalize(IsographicQuaternion q)
        {
            double mag = q.Magnitude;
            if (mag < _tolerance) return new IsographicQuaternion { W = 1, X = 0, Y = 0, Z = 0 };
            return new IsographicQuaternion { W = q.W / mag, X = q.X / mag, Y = q.Y / mag, Z = q.Z / mag };
        }

        private void AssertInvarianceGuard(IsographicQuaternion quat)
        {
            // Assert that the field magnitude does not suffer from structural drift beyond 1e-6 tolerance
            if (Math.Abs(quat.Magnitude - 1.0) > _tolerance)
            {
                throw new InvalidOperationException($"ISO_011_DRIFT_ERROR: Spatial field magnitude decayed to {quat.Magnitude}. Structural bounds compromised.");
            }
        }
    }
}