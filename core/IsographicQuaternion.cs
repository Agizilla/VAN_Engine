using System;

namespace VAN_Engine.Core
{
    /// <summary>
    /// Isographic Quaternion with coupled dimensions (Sound-Shape, Sound-Number, Shape-Time, Number-Time)
    /// ISO_009: Quadruple Mapping
    /// </summary>
    public struct IsographicQuaternion
    {
        public double W { get; set; } // Sound-Shape coupling
        public double X { get; set; } // Sound-Number coupling
        public double Y { get; set; } // Shape-Time coupling
        public double Z { get; set; } // Number-Time coupling

        public IsographicQuaternion(double w, double x, double y, double z)
        {
            W = w;
            X = x;
            Y = y;
            Z = z;
        }

        // Projection methods for specific queries
        public double GetSoundProjection() => Math.Sqrt(W * W + X * X);
        public double GetShapeProjection() => Math.Sqrt(W * W + Y * Y);
        public double GetNumberProjection() => Math.Sqrt(X * X + Z * Z);
        public double GetTimeProjection() => Math.Sqrt(Y * Y + Z * Z);

        // Global magnitude (must preserve across round-trips)
        public double Magnitude => Math.Sqrt(W * W + X * X + Y * Y + Z * Z);

        // Normalization
        public IsographicQuaternion Normalize()
        {
            double mag = Magnitude;
            if (mag < 1e-10) return this;
            return new IsographicQuaternion(W / mag, X / mag, Y / mag, Z / mag);
        }

        // Quaternion multiplication (for transit modifiers)
        public static IsographicQuaternion operator *(IsographicQuaternion a, IsographicQuaternion b)
        {
            return new IsographicQuaternion(
                a.W * b.W - a.X * b.X - a.Y * b.Y - a.Z * b.Z,
                a.W * b.X + a.X * b.W + a.Y * b.Z - a.Z * b.Y,
                a.W * b.Y - a.X * b.Z + a.Y * b.W + a.Z * b.X,
                a.W * b.Z + a.X * b.Y - a.Y * b.X + a.Z * b.W
            );
        }

        // Equality with tolerance
        public bool ApproxEquals(IsographicQuaternion other, double tolerance = 1e-6)
        {
            return Math.Abs(W - other.W) < tolerance &&
                   Math.Abs(X - other.X) < tolerance &&
                   Math.Abs(Y - other.Y) < tolerance &&
                   Math.Abs(Z - other.Z) < tolerance;
        }

        public override string ToString() => $"Q({W:F3}, {X:F3}, {Y:F3}, {Z:F3})";
    }
}
